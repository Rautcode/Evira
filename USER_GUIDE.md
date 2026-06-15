# SCADA Assistant: Complete User Guide

Welcome to the **SCADA Assistant**, your central command center for real-time factory telemetry monitoring, automated reporting, and machine diagnostics. 

This guide will walk you through exactly how to connect this application to your real factory floor, generate your first report, and automate your workflows.

---

## 1. Initial Setup & Launch
Before using the web interface, ensure the backend and frontend servers are running on your host machine.

1. **Start the Backend (Python/FastAPI):**
   Navigate to the `backend` folder and run the server. It will automatically create your SQL database and tables.
   ```bash
   cd backend
   python app/main.py
   # Or run via uvicorn: uvicorn app.main:app --reload
   ```

2. **Start the Frontend (Next.js):**
   Navigate to the `src` folder and start the web application.
   ```bash
   npm run dev
   ```

3. **Open the Application:**
   Open your web browser and navigate to `http://localhost:3000`.

---

## 2. Connecting to Your Factory (No-Code Setup)
You do not need to edit any code or configuration files to connect to your factory floor. Everything is handled directly through the web interface.

### Step 2.1: Open System Settings
1. On the left sidebar menu, click on **Settings**.
2. Scroll down to the **System Configuration Forms**.

### Step 2.2: Connect the SCADA OPC UA Server
1. In the **SCADA OPC UA Connection** panel, enter your real Siemens WinCC or PLC server address (e.g., `opc.tcp://192.168.1.100:4840`).
2. If your server requires a username and password, enter them in the optional fields.

### Step 2.3: Connect the SQL Database
1. In the **SQL Database Connection** panel, enter the IP address of your MS SQL Server (e.g., `192.168.1.50`).
2. Set the database name (default: `scada_reports`).
3. Select your Authentication Method (Windows Active Directory or SQL Server Account) and provide credentials if prompted.

### Step 2.4: Save & Hot-Reload
Click the blue **"Connect Systems & Hot-Reload"** button at the bottom of the page. 
*Magic happens here:* The application will instantly disconnect from any old servers, connect to your real factory IP addresses, and begin streaming live telemetry data without you having to reboot the application!

---

## 3. Understanding Auto-Discovery
Once connected, navigate to the **Settings** page and look at the **Auto-Discovered SCADA Tags** table.

The backend application automatically crawls your WinCC server and discovers all variables (tags). It uses smart rules to map them to your factory machines:
- Tags containing "Extruder" are mapped to Machine **M001**.
- Tags containing "Temp" are mapped as **Temperature (°C)**.
- Tags containing "Press" are mapped as **Pressure (bar)**.

You can view the live, real-time values of your factory machines ticking up and down on this page.

---

## 4. Generating Reports
The core feature of SCADA Assistant is converting raw telemetry into beautiful corporate PDF reports.

### Step 4.1: Customizing Templates
1. Click on **Templates** in the sidebar.
2. Here, you can define the JSON structure of your reports. You can create custom layouts, add corporate headers, and choose which data columns (like Voltage, Pressure, Speed) to display.
3. Save your template to make it available for the Generator.

### Step 4.2: Using the Report Generator
1. Click on **Report Generator** in the sidebar.
2. Follow the 3-step wizard:
   - **Step 1 (Scope):** Select the Machine (e.g., M001 - Extruder), the Shift (Morning/Evening/Night), and the Date Range.
   - **Step 2 (Format):** Choose the report type (Production Summary, Quality Metrics, etc.), pick your custom Template, and decide if you want a PDF or CSV export. You can also toggle "Include Charts".
   - **Step 3 (Preview):** Review the raw data table fetched directly from the SQL database to ensure it looks correct.
3. Click **Generate Final Report**. Your browser will automatically download the polished PDF or CSV.

---

## 5. Automating Tasks (The Scheduler)
Why generate reports manually when the system can do it for you while you sleep?

1. Click on **Scheduler** in the sidebar.
2. Click **Create New Task**.
3. Choose what you want to automate (e.g., "Daily Production Summary").
4. Select the trigger type:
   - **Cron:** Set it to run every day at 6:00 AM (`0 6 * * *`).
   - **Interval:** Set it to run every 8 hours.
5. Provide the email addresses of the managers who should receive the report.
6. Click **Save**. The backend will now automatically generate the PDF at the specified time and email it out using the SMTP settings you configured on the Settings page.

---

## 6. System Diagnostics & Troubleshooting
If data stops flowing or reports fail to generate, navigate to the **Dashboard**.

On the right side of the Dashboard, you will see the **System Diagnostics** panel. This checks the real-time heartbeat of all 4 major subsystems:
1. **Database Link:** If this shows "Disconnected", check your SQL server IP and credentials in Settings.
2. **WinCC Interface:** If this shows "Offline", check if the factory PLC network is down or if the OPC UA server URL changed.
3. **Email Dispatcher:** If this shows "Degraded", ensure you have saved a valid Gmail/Outlook App Password in the Settings page.
4. **Report Compiler:** Confirms the PDF rendering engine is healthy.

You can also view the **Recent Activity Stream** on the dashboard to see chronological logs of any errors or system events.
