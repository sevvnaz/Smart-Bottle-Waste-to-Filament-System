# RecyPrint – Smart Bottle Waste-to-Filament System
## Final Project Report

---

## 5.3 Performance Evaluation

The system was evaluated against the success criteria defined in the project proposal. Quantitative metrics were used where possible to assess whether each criterion was met.

| Success Criterion | Target Value | Achieved Value | Met? |
|---|---|---|---|
| SC-1: Real-time data update latency | < 2 seconds | ~0.5–1 second | ✅ Yes |
| SC-2: MQTT communication reliability | Continuous stable connection | Stable communication with no major interruptions | ✅ Yes |
| SC-3: Data logging reliability (cloud + local) | No data loss during operation | Data successfully logged in Neon DB with SQLite fallback | ✅ Yes |
| SC-4: System responsiveness (start/stop commands) | < 2 second response time | Immediate response observed | ✅ Yes |

---

## 5.4 User Feedback

No formal user testing protocol was conducted within the scope of this project. However, informal feedback was collected from team members and supervisors throughout the development and integration phases. The feedback generally indicated that the dashboard interface was intuitive and easy to operate, and that the real-time visualizations provided clear and useful information about the extrusion process. Based on this feedback, minor improvements were made to the layout of the control panel and the formatting of displayed sensor values.

---

## 6. Results and Discussion

### 6.1 Final Results

The RecyPrint system was successfully completed and demonstrated as a functional IoT-based monitoring and control platform for a plastic extrusion process. The following results were achieved:

- The **live dashboard** displayed real-time sensor readings (temperature, motor speed, and filament diameter) with minimal latency via MQTT and WebSocket communication.
- **Start/Stop extrusion commands** were successfully transmitted from the web interface to the hardware through the MQTT broker.
- **All sensor data** was logged reliably to the Neon PostgreSQL cloud database, with an SQLite fallback ensuring data integrity during connectivity issues.
- The **CSV export feature** allowed historical sensor logs to be downloaded and analyzed externally.
- The **closed-loop diameter control** algorithm maintained filament diameter near the 1.75 mm target by automatically adjusting motor speed via the `bridge.py` controller.
- The **emergency stop** feature triggered correctly when temperature exceeded the 200°C safety threshold.
- A **secure session-based user authentication system** was implemented to protect the dashboard, logs, and CSV export routes from unauthorized remote operations.

---

### 6.2 Analysis and Discussion

The results obtained from testing and system evaluation indicate that the RecyPrint platform successfully meets its primary objective of providing a reliable software infrastructure for real-time monitoring, remote control, and data management of the extrusion process.

One of the most successful aspects of the system is the real-time communication enabled by MQTT. The publish-subscribe architecture allowed efficient and continuous data exchange between the hardware, backend, and frontend components. This resulted in smooth real-time visualization of process parameters such as temperature, motor speed, and filament diameter. The system demonstrated low latency and stable performance under normal operating conditions.

Another key strength of the system is its hybrid data storage strategy. By combining a cloud-based PostgreSQL database (Neon.tech) with a local SQLite fallback, the system ensured that no sensor data would be lost even in the event of a network interruption. This design choice significantly improved the reliability and robustness of the logging system.

The closed-loop diameter control algorithm embedded in `bridge.py` was also a notable achievement. By using proportional feedback control, the system was able to automatically adjust motor speed based on real-time filament diameter readings, reducing the need for manual intervention and improving product consistency.

However, certain limitations were observed. The system's performance was dependent on the stability of the external MQTT broker (`broker.emqx.io`), which introduced a potential single point of failure. Additionally, the diameter sensor required calibration before each session, which added a minor operational overhead. In a production environment, these issues could be addressed by deploying a private MQTT broker and implementing auto-calibration routines.

Compared to similar existing solutions in the literature, the RecyPrint system achieved a competitive level of integration between hardware control and cloud-based data management. Most comparable systems either rely on proprietary platforms or lack real-time web interfaces. RecyPrint's use of open-source technologies and standard IoT protocols makes it a cost-effective and extensible alternative.

---

### 6.3 Comparison with Original Objectives

The RecyPrint project was initially defined with the objective of developing a software-based IoT system for real-time monitoring, remote control, and reliable data management of a plastic extrusion process. Based on the results obtained, the system was evaluated against these objectives.

**Real-time Monitoring:**
The objective of providing real-time monitoring of key process parameters (temperature, motor speed, and filament diameter) was **fully achieved**. The MQTT-based communication enabled continuous data streaming, and the web dashboard successfully displayed live system data with acceptable latency.

**Remote Control:**
The objective of enabling remote control of the extrusion process (start/stop operations and parameter adjustments) was also **fully met**. The system allowed users to issue commands through the web interface, which were immediately transmitted to the hardware via the MQTT broker.

**Data Management and Logging:**
The objective of maintaining a reliable and persistent data logging system was **fully achieved**. Sensor readings were stored in the Neon PostgreSQL cloud database in real time, and a local SQLite fallback ensured continuity during any network disruptions.

**Safety and Fault Handling:**
The software-level safety objective, including automatic emergency stop on temperature limit exceedance, was **fully implemented** and verified during testing.

**Scalability and Extensibility:**
While the current system is functional within its intended scope, the objective of long-term scalability was only **partially addressed** due to reliance on a third-party public MQTT broker. Deploying a dedicated broker would be the next step toward a fully production-ready system.

---

## 7. Project Management

### 7.1 Work Breakdown and Schedule

*(Place your Gantt Chart image here)*  
**Figure 7.1:** RecyPrint final Gantt chart comparing the project schedule and completed task durations across the 15-week academic semester.

The Gantt chart illustrates the final timeline of the RecyPrint project across all mechatronic and software development phases. All planned tasks were successfully completed within the 15-week semester timeline:

*   **Parallel Design Phase (Weeks 1–7):** During the early stages, the software team developed the base Software Architecture & DB (Weeks 3–5) and Backend API Dev (Weeks 5–9) in parallel with the mechatronics team's Mechanical Design & Parts and Electronics assembly. This decoupled strategy prevented development bottlenecks by utilizing simulated data loops to test backend logic before hardware was physically active.
*   **Interface & Firmware Alignment (Weeks 6–11):** The Frontend Dashboard (Weeks 7–11) was developed synchronously with the mechatronics team's Firmware Development (Weeks 6–10). Standardized JSON schemas were defined during this phase to establish a strict communication contract.
*   **System Integration Phase (Weeks 11–13):** The transition from simulated endpoints to active physical hardware integration occurred during System Integration. Minor schedule deviations were experienced here due to initial serial communication latency and packet serialization errors. These challenges were resolved by implementing the tethered Python bridge middleware to handle MQTT packaging.
*   **Testing & Optimization (Weeks 13–15):** The final weeks focused on reliability and security hardening. It was during this phase that the software team implemented the secure WebSocket migration (WSS port 8084) to resolve Render cloud mixed-content blocking, and deployed the local SQLite fallback database (`local_cache.db`) to handle laboratory network outages.

Overall, the project adhered closely to the planned schedule, and all core mechatronic and software functionalities were successfully completed on time.

---

### 7.2 Individual Contributions

The development of the RecyPrint software and IoT infrastructure was executed via a structured division of labor, ensuring that architectural design, visual layout, data integrity, and protocol integration were handled by dedicated engineers.

| Team Member | Department | Key Technical Focus Areas | Overall Effort (%) |
| :--- | :--- | :--- | :--- |
| **Şevval Naz Savaş** | Software Engineering | Frontend Architecture, MQTT/WebSocket Data Binding, Real-time Charting, Control & Safety Logic Implementation. | **%40** |
| **Eda Yaygılı** | Software Engineering | UI/UX Design System (Glassmorphism), Historical Data Management, CSV Export API, DB Schema Design (PostgreSQL/SQLite). | **%33** |
| **Selen Göğüş** | Software Engineering | Template Structuring, Data Validation, Functional Testing, MQTT Payload Integration & Verification. | **%27** |

#### Detailed Engineering Contributions:

*   **Şevval Naz Savaş (Lead Frontend & IoT Integration — %40 Effort):**
    Şevval was responsible for the core frontend architecture and real-time communication stack. During the Interface Alignment phase (Weeks 7–11), she designed and implemented the native WebSockets and MQTT pipeline to ensure zero-latency telemetry rendering. She configured the **Chart.js** dynamic updates for both temperature and filament diameter profiles. On the control side, she coded the state-management logic for the Start/Stop command dispatches, calibrated the Tare button interface, and implemented the frontend safety trigger that alerts users with a red visual overlay during a critical temperature threshold violation (>200°C).

*   **Eda Yaygılı (Lead UI/UX & Data Systems — %33 Effort):**
    Eda directed the visual identity and data export infrastructure of the RecyPrint dashboard. She built the responsive grid structure and custom **Glassmorphism CSS design system**, ensuring readability in laboratory environments. In the Testing & Optimization phase (Weeks 13–15), Eda developed the historical data portal (`/history`), designing the table structures and writing the backend routing to process and export Postgres records into standardized **CSV/Excel formats**. She also collaborated with backend database designs, ensuring proper query performance for multi-point history fetches.

*   **Selen Göğüş (QA & Data Verification — %27 Effort):**
    Selen focused on system validation, integration testing, and documentation templates. She played a key role during the Integration Phase (Weeks 11–13) by writing automated payload test scripts to verify the schema integrity of incoming ESP32 serial data. Selen executed the validation runs comparing MQTT communication latency against the target threshold (SC-1), verifying that no data loss occurred during simulated connection drops. She also set up the initial document structures and conducted UI compatibility testing across different browser engines to ensure styling consistency.

---

### 7.3 Inter-Departmental Collaboration Assessment

The RecyPrint project required close collaboration between the software and mechatronics sub-teams to successfully develop a fully integrated smart extrusion system. The effectiveness of this interdisciplinary approach played a critical role in achieving the project objectives.

One of the strongest aspects of the collaboration was the clear separation of responsibilities. The mechatronics team focused on hardware components such as sensors, motor control, and physical extrusion mechanisms, while the software engineering team was responsible for developing the backend system, communication infrastructure, and user interface. This division allowed each team to work efficiently within their domain of expertise.

Communication between teams was primarily maintained through shared data formats and well-defined interfaces, particularly through the use of MQTT-based JSON messages. This standardized communication protocol enabled seamless data exchange between hardware and software components, reducing integration complexity.

However, some challenges were encountered during the integration phase. Differences in development pace between hardware and software components occasionally caused synchronization issues. Additionally, debugging real-time communication between systems required iterative testing and coordination between both teams.

Despite these challenges, the collaboration proved to be effective overall. The iterative development process and continuous feedback between teams allowed issues to be identified and resolved efficiently. The integration of hardware and software components was successfully completed, resulting in a functional and reliable system.

In conclusion, the joint-department approach significantly contributed to the success of the project. While minor improvements could be made in terms of early-stage coordination and synchronization, the collaboration between the teams was strong and enabled the successful delivery of the RecyPrint system.

---

### 7.4 Budget and Resources

The software and IoT subsystem of the RecyPrint project was developed with a primary focus on cost-efficiency, scalability, and the utilization of modern open-source technologies. No direct financial budget was allocated for the software subsystem, and the development was successfully completed utilizing zero-cost resources.

A breakdown of the open-source tools, protocols, and platforms leveraged in this project is detailed below:

| Resource Type | Technology Used | Cost / License | Role in the Project |
| :--- | :--- | :--- | :--- |
| **Programming Language** | Python 3 | Free / Open Source | Core language for the backend and smart hardware bridge. |
| **Backend Framework** | Flask | Free / Open Source | Hosts the local server, manages endpoints, and runs background threads. |
| **Communication Protocol** | MQTT (`broker.emqx.io`) | Free Public Broker | Facilitates real-time, low-latency publish-subscribe telemetry. |
| **Cloud Database** | Neon PostgreSQL | Free Tier (AWS Cloud) | Primary persistent data storage for historical logging. |
| **Local Database** | SQLite | Free / Open Source | Offline fallback database for local data integrity. |
| **Frontend Stack** | HTML5, CSS3, Vanilla JavaScript | Free / Open-source Standards | Renders the responsive glassmorphism dashboard UI. |
| **Data Visualization** | Chart.js | Free / MIT License | Generates live temperature and filament diameter graphs. |
| **Development Tools** | VS Code & Modern Web Browsers | Free | Code editing, debugging, and testing interfaces. |

#### Physical & Hardware Resources
From a resource perspective, development and testing relied on standard personal computers and existing internet connections. While the mechatronic hardware components (such as the ESP32 microcontroller, L298N motor driver, band heaters, and optical sensors) were funded separately under the mechatronics budget, the software subsystem required zero additional physical infrastructure or paid software subscriptions. 

By designing a lightweight, cloud-integrated architecture, the software team eliminated the need for hosting fees or specialized database servers, ensuring that the system remains highly accessible, reproducible, and easy to deploy for future academic or open-source initiatives.

---

## 8. Ethical, Safety, and Sustainability Considerations

The RecyPrint project incorporates several ethical, safety, and sustainability considerations throughout its design and implementation to ensure a responsible, secure, and reliable operation.

### 8.1 Ethical Considerations
*   **Privacy and Data Protection:** From an ethical perspective, the RecyPrint system does not collect, process, or store any personal data or interact with human subjects. All transmitted telemetry consists strictly of technical machine parameters—specifically temperature, motor speed, and filament diameter. Thus, no privacy risks or data protection issues exist.
*   **Open-Source Integrity:** The entire system is built utilizing open-source and transparent technologies (Flask, Paho-MQTT, SQLite, PostgreSQL, Chart.js). This ensures that the code can be fully audited, verified, and extended by other researchers, promoting transparency and collaborative engineering ethics.

### 8.2 Safety Considerations
Safety was treated as a core design requirement rather than an afterthought. Several software-level safety mechanisms were designed and verified:
*   **Automated Temperature Threshold (200°C Limit):** The local bridge continuously monitors the temperature data. If the nozzle exceeds the 200°C safety limit, the system enters emergency mode, immediately sending shutdown commands (`M0`/`T0`) to turn off the heater and motor without user intervention.
*   **Immediate Remote Shutdown:** The dashboard includes an emergency Stop button that allows operators to instantly send shutdown directives to the physical machine, enabling rapid manual response to anomalies.
*   **Secure Remote Access Control:** To prevent unauthorized operators from accessing the controls and triggering the physical extrusion machinery remotely (which poses high thermal and mechanical safety hazards), a secure session-based authentication screen was implemented. Credentials are loaded dynamically via environment variables to prevent password exposure.
*   **Startup Speed Lock:** The proportional controller in the bridge locks the motor speed at 125 PWM until the filament diameter exceeds 1.0 mm, preventing high-speed motor startups before material reaches the sensor.
*   **Tare Sensor Calibration:** A dedicated "Tare Gauge" button allows operators to calibrate/zero the optical diameter sensor, preventing sensor drift from causing erratic motor acceleration.

### 8.3 Sustainability Considerations
*   **Circular Economy Alignment:** The system directly supports environmental sustainability by recycling plastic PET bottle waste into high-quality 3D printing filament, reducing plastic pollution and landfill accumulation.
*   **Resource and Energy Efficiency:** The database uses a hybrid storage strategy (Neon PostgreSQL cloud + local SQLite buffer) to prevent data loss without redundant hardware. Communication is handled via MQTT, which utilizes a lightweight publish-subscribe model that minimizes network bandwidth and reduces overall energy consumption.

---

## 9. Conclusions

### 9.1 Summary of Achievements

The RecyPrint project successfully achieved its primary objective of developing a fully functional, software-driven, and cloud-integrated smart extrusion monitoring and control system. By establishing a robust digital bridge between mechatronic hardware and a modern web infrastructure, the project accomplished several key engineering milestones:

*   **Low-Latency Real-Time Telemetry:** Implemented an MQTT publish-subscribe architecture that streams multivariable telemetry (extrusion temperature, motor speed, and filament diameter) from the hardware to the web dashboard with an average latency of ~0.5–1.0 second, meeting the strict SC-1 and SC-2 performance criteria.
*   **Closed-Loop Process Automation:** Designed and integrated a proportional feedback control loop within the `bridge.py` middleware. This system automatically adjusts the motor speed (PWM) based on live opto-electronic sensor diameter readings, maintaining filament production close to the target 1.75 mm standard without manual intervention.
*   **Fault-Tolerant Hybrid Data Logging:** Created a resilient data architecture combining a primary cloud-based PostgreSQL database (Neon.tech) with a local, zero-config SQLite database (`local_cache.db`). This hybrid strategy prevents data loss by caching records locally during network dropouts and syncing them to the cloud once connection is restored.
*   **Multi-Tier Safety Safeguards:** Implemented a software-level emergency shutdown protocol that instantly triggers when the heater exceeds the critical safety threshold of 200°C. The system transmits immediate shutdown directives (`M0`/`T0`) to the ESP32, flags the web dashboard with a prominent red emergency overlay, and suspends closed-loop motor adjustments to prevent hardware damage.
*   **Enhanced UX, Portability & Data Export:** Developed a responsive, glassmorphism-themed dark dashboard that includes synchronized real-time graphs for both temperature and diameter. The system also features a dedicated data portal allowing researchers to download historical logs as standardized CSV/Excel spreadsheets with a single click.
*   **Secure Web Access & Authentication:** Integrated a Flask session-based user authentication layer that protects all routes (dashboard, logs, CSV export) from unauthorized access, allowing the mechatronics laboratory machinery to be controlled remotely only by verified personnel.

In conclusion, the RecyPrint system demonstrates that modern open-source web technologies and lightweight IoT protocols can be successfully integrated to build reliable, safe, and sustainable industrial recycling prototypes at zero software licensing costs.

---

*RecyPrint Capstone Project — Software Engineering Team*
*Şevval Naz Savaş · Eda Yaygılı · Selen Göğüş*
