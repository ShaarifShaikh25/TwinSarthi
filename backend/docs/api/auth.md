# Authentication & RBAC API Specification

## 1. Overview
POLAR-TWIN employs JWT (JSON Web Token) bearer authentication with Role-Based Access Control (RBAC) across three distinct operational roles:

| Role | Permissions | Permitted Actions |
|---|---|---|
| **ADMIN** | Full administrative access | Create stations, user management, system threshold configs, all mutations |
| **CONTROLLER** | Operational command access | View digital twins, execute simulations, approve / modify / reject recommendations, register equipment / sensors / inventory |
| **VIEWER** | Read-only observational access | View stations, twins, telemetry, alerts, and historical intelligence. Mutation requests return `403 Forbidden` |

---

## 2. Endpoints

### 2.1 User Login
`POST /api/auth/login`

Authenticates credentials and returns a signed JWT access token.

#### Request Body
```json
{
  "username": "controller",
  "password": "controllerpassword"
}
```

#### Response (`HTTP 200`)
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in_minutes": 60,
    "user": {
      "id": 2,
      "username": "controller",
      "email": "controller@polartwin.ncpor.res.in",
      "role": "CONTROLLER"
    }
  }
}
```

---

### 2.2 Current User Profile
`GET /api/auth/me`

Returns the authenticated identity and assigned privileges.

#### Headers
```
Authorization: Bearer <access_token>
```

#### Response (`HTTP 200`)
```json
{
  "success": true,
  "data": {
    "id": 2,
    "username": "controller",
    "email": "controller@polartwin.ncpor.res.in",
    "role": "CONTROLLER",
    "is_active": true,
    "created_at": "2026-09-29T10:00:00Z"
  }
}
```

---

## 3. Seeded Accounts for Testing

| Username | Password | Role |
|---|---|---|
| `admin` | `adminpassword` | `ADMIN` |
| `controller` | `controllerpassword` | `CONTROLLER` |
| `viewer` | `viewerpassword` | `VIEWER` |
