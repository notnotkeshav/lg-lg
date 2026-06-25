import json

import frappe


@frappe.whitelist()
def create_record():
    """For Creating Any Kind Of Record"""
    try:
        if frappe.request.method != "POST":
            frappe.throw("Only POST requests are allowed")

        data = json.loads(frappe.request.data)

        # check model is availble or not
        if data.get("model") == None:
            frappe.throw("Model is required")

        # create a new document
        doctype = data.get("model")
        document_data = data.get("data")

        if doctype == "CRM Deal":
            # 1. Get The Deal Structure
            doctype = "CRM Deal"
            crm_deal_model_field = get_doc_and_return_detail_fields(doctype=doctype)
            doc, _ = handle_crm_deal(
                document_data, crm_deal_model_field, doctype=doctype
            )
        else:
            document_data["doctype"] = doctype
            doc = frappe.get_doc(document_data)
            doc.insert()
        return {
            "status": "success",
            "data": {"model": doctype, "data": document_data, "doc": doc.as_dict()},
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Test API Error")
        frappe.response.http_status_code = 400
        return {"status": "error", "message": str(e)}


def handle_crm_deal(document_data, crm_deal_model_field, doctype="CRM Deal"):
    """Handle CRM Deal creation with strict format validation for foreign keys and tables."""

    # 1. Check mandatory fields
    mandatory_fields = list(
        filter(lambda field: field.get("mandatory") == "Yes", crm_deal_model_field)
    )
    for field in mandatory_fields:
        field_name = field.get("api_key")
        if field_name not in document_data:
            frappe.throw(
                f"Mandatory field '{field_name}' is missing in the document data."
            )

    # 2. Validate and handle fields
    for api_key, api_value in document_data.items():
        finded_field = next(
            (
                field
                for field in crm_deal_model_field
                if field.get("api_key") == api_key
            ),
            None,
        )
        if not finded_field:
            frappe.throw(
                f"Field '{api_key}' is not a valid field in the linked document data for '{doctype}'."
            )

        # --- Handle Foreign Key ---
        if finded_field.get("fieldtype") == "Foreign Key":
            if not isinstance(api_value, dict):
                frappe.throw(
                    f"Invalid format for field '{api_key}': Expected a dictionary for Foreign Key."
                )

            linked_doctype = finded_field.get("options")
            id_field_finded = next(
                (
                    f
                    for f in (
                        finded_field.get("fields", [])
                        if linked_doctype != doctype
                        else crm_deal_model_field
                    )
                    if f.get("id_field") == True
                ),
                None,
            )
            naming_rule = frappe.get_meta(linked_doctype).get("naming_rule")

            if naming_rule != "Expression":
                if not id_field_finded:
                    frappe.throw(
                        f"Mandatory id field is missing in the linked document data for '{api_key}'."
                    )
                if id_field_finded.get("api_key") not in api_value:
                    frappe.throw(
                        f"Mandatory id field '{id_field_finded.get('api_key')}' is missing in the linked document data for '{api_key}'."
                    )

            _, saved_value = handle_crm_deal(
                api_value,
                (
                    finded_field.get("fields", [])
                    if linked_doctype != doctype
                    else crm_deal_model_field
                ),
                doctype=linked_doctype,
            )
            document_data[api_key] = saved_value

        # --- Handle Table Fields ---
        elif finded_field.get("fieldtype") == "Table":
            if not isinstance(api_value, list):
                frappe.throw(
                    f"Invalid format for table field '{api_key}': Expected a list of dictionaries."
                )

            processed_table = []
            for row in api_value:
                if not isinstance(row, dict):
                    frappe.throw(
                        f"Invalid row format in table '{api_key}': Each row must be a dictionary."
                    )

                for child_key, child_val in row.items():
                    # Mandatory field check for child table

                    if isinstance(child_val, dict):
                        child_field_meta = next(
                            (
                                f
                                for f in finded_field.get("fields", [])
                                if f.get("api_key") == child_key
                            ),
                            None,
                        )
                        if (
                            child_field_meta
                            and child_field_meta.get("fieldtype") == "Foreign Key"
                        ):
                            id_field_finded = next(
                                (
                                    f
                                    for f in child_field_meta.get("fields", [])
                                    if f.get("id_field") == True
                                ),
                                None,
                            )
                            linked_doctype = child_field_meta.get("options")
                            # naming_rule = frappe.get_meta(linked_doctype).get(
                            #     "naming_rule"
                            # )

                            # if naming_rule != "Expression":
                            #     if not id_field_finded:
                            #         frappe.throw(
                            #             f"Mandatory id field is missing in child table '{api_key}' → field '{child_key}'"
                            #         )
                            #     if id_field_finded.get("api_key") not in child_val:
                            #         frappe.throw(
                            #             f"Mandatory id field '{id_field_finded.get('api_key')}' is missing in child table '{api_key}'"
                            #         )

                            # before checking foreign key data first will check that value already exist or not
                            _, saved_value = handle_crm_deal(
                                child_val,
                                child_field_meta.get("fields", []),
                                doctype=linked_doctype,
                            )
                            row[child_key] = saved_value

                processed_table.append(row)
            document_data[api_key] = processed_table

        # --- Handle Primitive Fields (valid field but not Foreign Key or Table) ---
        elif isinstance(api_value, (str, int, float, bool, type(None))):
            continue  # valid primitive value

        else:
            frappe.throw(
                f"Invalid format for field '{api_key}'. Unexpected value type."
            )

    # 3. Final validation: unknown fields already handled above

    # 4. Save or update document
    id_field_finded = next(
        (field for field in crm_deal_model_field if field.get("id_field") == True), None
    )
    finded_val = (
        document_data.get(id_field_finded.get("api_key")) if id_field_finded else None
    )
    document_exist = frappe.db.exists(doctype, finded_val)

    if document_exist:
        value_document = frappe.get_doc(doctype, finded_val)
        value_document.update(document_data)
        return (value_document.save(), finded_val)
    else:
        value_document = frappe.new_doc(doctype)
        value_document.update(document_data)
        return (value_document.insert(), finded_val)


hide_fields = [
    "creation",
    "modified",
    "modified_by",
    "owner",
    "docstatus",
    "idx",
    "name",
    "parent",
    "parentfield",
    "parenttype",
    "Section Break",
    "Tab Break",
]

not_show_type = ["Column Break", "Section Break", "Tab Break"]

show_fields = [
    {"fieldname": "api_key"},
    {"label": "label_name"},
    {"fieldtype": "fieldtype"},
    {"options": "options"},
    {"reqd": "mandatory"},
    {"name": "id_field"},
]


@frappe.whitelist()
def get_model_detail():
    """For Getting Fields of any kind of Doctype"""
    try:
        if frappe.request.method != "POST":
            frappe.throw("Only POST requests are allowed")

        data = json.loads(frappe.request.data)

        # check model is availble or not
        doctype = data.get("model")
        return get_doc_and_return_detail_fields(doctype=doctype)

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Test API Error")
        frappe.response.http_status_code = 400
        return {"status": "error", "message": str(e)}


def get_doc_and_return_detail_fields(doctype):
    if doctype == None:
        frappe.throw("Model is required")

    # get header table
    is_deal = doctype == "CRM Deal"
    fields = get_fields_by_doctype(
        doctype=doctype, is_deal=is_deal, module_called=[], hashmap={}, table_hashmap={}
    )

    # get child table fields
    fields = list(
        map(
            lambda field: check_table_or_return_same_fields(
                field=field,
                is_deal=is_deal,
                module_called=[],
                hashmap={},
                table_hashmap={},
            ),
            fields,
        )
    )
    return fields


def check_table_or_return_same_fields(
    field, is_deal=False, module_called=[], hashmap={}, table_hashmap={}
):
    """Check if field is table or not"""
    if field.get("fieldtype") == "Table":
        # get child table fields
        if field.get("options") in table_hashmap:
            child_table_fields = table_hashmap[field.get("options")]
            field["fields"] = child_table_fields
        else:
            child_table_fields = get_fields_by_doctype(
                field.get("options"), is_deal, module_called, hashmap, table_hashmap
            )
            child_table_fields = list(
                map(
                    lambda field: check_table_or_return_same_fields(
                        field, is_deal, module_called, hashmap, table_hashmap
                    ),
                    child_table_fields,
                )
            )
            table_hashmap[field.get("options")] = child_table_fields
            field["fields"] = child_table_fields
    return field


def get_fields_by_doctype(
    doctype, is_deal=False, module_called=[], hashmap={}, table_hashmap={}
):
    if doctype in hashmap:
        return hashmap[doctype]

    if doctype in module_called:
        return []
    module_called.append(doctype)
    """Get fields by doctype"""
    meta = frappe.get_meta(doctype).as_dict()
    if meta.get("fields") == None:
        return []

    rule_by_field_name = meta.get("naming_rule") == "By fieldname"
    field_name = None
    if rule_by_field_name:
        field_name_exist = meta.get("autoname")
        if field_name_exist:
            field_name = field_name_exist.split(":")[1]
    get_fields = create_mapped_fields(meta.get("fields", []), field_name)

    if is_deal == True:
        for field in get_fields:
            if field.get("fieldtype") == "Foreign Key":
                field["fields"] = get_fields_by_doctype(
                    field.get("options"), is_deal, module_called, hashmap, table_hashmap
                )
            # elif field.get("fieldtype") == "Table":
            #     child_table_fields = check_table_or_return_same_fields(field, is_deal, module_called, table_hashmap)
            #     table_hashmap[field.get("options")] = child_table_fields
            #     field["fields"] = child_table_fields
    hashmap[doctype] = get_fields
    return get_fields


def create_mapped_fields(fields, field_name="NOT_FOUND"):
    fields = list(
        map(
            lambda field: (
                {**field, "name": True}
                if field.get("fieldname") == field_name
                else field
            ),
            fields,
        )
    )
    """Create mapped fields"""
    mapped_fields = [
        {
            transform_key(key): transform_key(key=key, value=value, need_value=True)
            for key, value in field.items()
            if check_availble_field(key)
        }
        for field in fields
        if check_not_availble_field(field)
    ]
    return mapped_fields


def transform_key(key, value=None, need_value=False):
    """Transform key to show fields"""
    keys_in_list = list(map(lambda field: list(field.keys())[0], show_fields))
    if key in keys_in_list:
        key_index = keys_in_list.index(key)
        if need_value == True:
            if key == "reqd":
                if value == 1:
                    return "Yes"
                else:
                    return "No"
            return transform_value(value)
        return list(show_fields[key_index].values())[0]
    return key


def transform_value(value):
    """Transform value to camel case"""
    if value == "Check":
        return "Boolean"
    elif value == "Data":
        return "String"
    elif value == "Select":
        return "Dropdown"
    elif value == "Int":
        return "Number"
    elif value == "Link":
        return "Foreign Key"
    return value


def check_availble_field(key):
    """Check if field is in show_fields"""
    if key in [list(field.keys())[0] for field in show_fields]:
        return True
    return False


def check_not_availble_field(field):
    """Check if field is not in hide_fields"""
    if field.get("fieldname") in hide_fields:
        return False
    elif field.get("hidden") == 1:
        return False
    elif field.get("fieldtype") in not_show_type:
        return False
    return True
