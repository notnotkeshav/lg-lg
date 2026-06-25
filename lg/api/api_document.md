<!-- Logos -->
<p align="center">
  <img src="https://lg.extensionerp.com/files/LG.png" alt="LG Logo" width="120"/>
  <img src="https://core.extensionerp.com/files/Extension-ERP-logoc9e95b.png" alt="Extension Technology Logo" width="160"/>
</p>

### 🧾 DOCUMENT TITLE  
**Master Module API Documentation**  
*Base URL: `https://lg.extensionerp.com`*

---

## 📌 Common Headers

```http
Content-Type: application/json
Authorization: token <api_key>:<api_secret>  # If authentication is enabled
````

---

# 🧑‍💼 CUSTOMER MODULE (`Customer`)

---

### 1️⃣ Create Customer

* **Endpoint:** `/api/method/lg.api.master_api.create_record`
* **Method:** `POST`
* **Description:** Create a new Customer record.

#### 📨 Request Body

```json
{
  "model": "Customer",
  "data": {
    "customer_name": "ABC Pvt Ltd",
    "customer_type": "Company",
    "customer_group": "Commercial",
    "territory": "India"
  }
}
```

#### ✅ Success Response

```json
{
  "message": "Record created successfully",
  "name": "CUST-0001"
}
```

---

### 2️⃣ Get Customer Fields

* **Endpoint:** `/api/method/lg.api.master_api.get_model_detail`
* **Method:** `POST`
* **Description:** Get metadata (fields & child tables) for `Customer`.

#### 📨 Request Body

```json
{
  "model": "Customer"
}
```

#### ✅ Success Response

```json
{
  "message": [
    {
      "api_key": "customer_name",
      "label_name": "Customer Name",
      "fieldtype": "Data",
      "mandatory": "Yes"
    },
    {
      "api_key": "customer_type",
      "label_name": "Customer Type",
      "fieldtype": "Select",
      "options": "Company\nIndividual",
      "mandatory": "Yes"
    }
  ]
}
```

---

### 3️⃣ Get Customer by Name

* **Endpoint:** `/api/method/lg.api.master_api.get_record_by_name`
* **Method:** `POST`
* **Description:** Fetch a customer using its unique ID.

#### 📨 Request Body

```json
{
  "model": "Customer",
  "name": "CUST-0001"
}
```

#### ✅ Success Response

```json
{
  "message": {
    "customer_name": "ABC Pvt Ltd",
    "customer_type": "Company"
  }
}
```

---

### 4️⃣ Get All Customers

* **Endpoint:** `/api/method/lg.api.master_api.get_all_records`
* **Method:** `POST`
* **Description:** Fetch all customer records.

#### 📨 Request Body

```json
{
  "model": "Customer"
}
```

#### ✅ Success Response

```json
{
  "message": [
    {
      "name": "CUST-0001",
      "customer_name": "ABC Pvt Ltd"
    },
    {
      "name": "CUST-0002",
      "customer_name": "XYZ Ltd"
    }
  ]
}
```

---

## ❌ Error Response Example

```json
{
  "exc_type": "ValidationError",
  "message": "Invalid model name"
}
```

---