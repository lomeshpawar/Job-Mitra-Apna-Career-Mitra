-- ========================================================
-- Job Mitra Portal - Database Schema & Seed Data (MySQL)
-- ========================================================

CREATE DATABASE IF NOT EXISTS `jobmitra_portal` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `jobmitra_portal`;

-- Drop existing tables if needed
DROP TABLE IF EXISTS `subscriptions`;
DROP TABLE IF EXISTS `applications`;
DROP TABLE IF EXISTS `bookmarks`;
DROP TABLE IF EXISTS `sent_emails`;
DROP TABLE IF EXISTS `candidate_profile`;
DROP TABLE IF EXISTS `jobs`;

-- 1. Jobs Table
CREATE TABLE `jobs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(255) NOT NULL,
    `company` VARCHAR(255) NOT NULL,
    `stream` VARCHAR(100) NOT NULL,
    `qualification` VARCHAR(255) NOT NULL,
    `city` VARCHAR(100) NOT NULL,
    `salary_min` INT NOT NULL,
    `salary_max` INT NOT NULL,
    `job_type` VARCHAR(50) DEFAULT 'Full Time',
    `experience` VARCHAR(50) DEFAULT 'Freshers / 0-1 yr',
    `skills_required` TEXT NOT NULL,
    `is_premium` TINYINT(1) DEFAULT 0,
    `is_urgent` TINYINT(1) DEFAULT 1,
    `is_verified` TINYINT(1) DEFAULT 1,
    `hr_email` VARCHAR(150) NOT NULL,
    `hr_phone` VARCHAR(50) NOT NULL,
    `address` VARCHAR(255) DEFAULT 'Industrial Hub, India',
    `description` TEXT NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Applications Table
CREATE TABLE `applications` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `job_id` INT NOT NULL,
    `candidate_name` VARCHAR(150) NOT NULL,
    `candidate_email` VARCHAR(150) NOT NULL,
    `candidate_phone` VARCHAR(50) NOT NULL,
    `candidate_stream` VARCHAR(100) DEFAULT '',
    `candidate_skills` TEXT,
    `cover_note` TEXT,
    `status` VARCHAR(50) DEFAULT 'Submitted',
    `applied_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`job_id`) REFERENCES `jobs`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Candidate Profile Table
CREATE TABLE `candidate_profile` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(150) NOT NULL DEFAULT 'Candidate User',
    `email` VARCHAR(150) NOT NULL DEFAULT 'candidate@graduate.in',
    `phone` VARCHAR(50) NOT NULL DEFAULT '+91 9876543210',
    `city` VARCHAR(100) NOT NULL DEFAULT 'Bengaluru',
    `stream` VARCHAR(100) NOT NULL DEFAULT 'Computer Science / IT',
    `education` VARCHAR(255) NOT NULL DEFAULT 'B.Tech / Graduate',
    `skills` TEXT NOT NULL,
    `is_premium` TINYINT(1) DEFAULT 1,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Bookmarks Table
CREATE TABLE `bookmarks` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `job_id` INT NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `unique_bookmark` (`job_id`),
    FOREIGN KEY (`job_id`) REFERENCES `jobs`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Sent Emails Log Table
CREATE TABLE `sent_emails` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `job_id` INT DEFAULT NULL,
    `recipient_email` VARCHAR(150) NOT NULL,
    `sender_email` VARCHAR(150) NOT NULL,
    `sender_name` VARCHAR(150) NOT NULL,
    `subject` VARCHAR(255) NOT NULL,
    `message` TEXT NOT NULL,
    `sent_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Subscriptions Table (UPI ID: 7770009027-2@axl)
CREATE TABLE `subscriptions` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `plan_name` VARCHAR(100) NOT NULL,
    `amount` INT NOT NULL,
    `upi_id` VARCHAR(100) NOT NULL DEFAULT '7770009027-2@axl',
    `utr_number` VARCHAR(100) NOT NULL,
    `candidate_email` VARCHAR(150) NOT NULL,
    `status` VARCHAR(50) DEFAULT 'Active',
    `subscribed_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Seed Default Candidate Profile
INSERT INTO `candidate_profile` (`name`, `email`, `phone`, `city`, `stream`, `education`, `skills`, `is_premium`)
VALUES (
    'Aditya Sharma',
    'aditya.engineer@jobmitra.in',
    '+91 9820012345',
    'Bengaluru',
    'Computer Science / IT',
    'B.Tech - Class of 2026',
    'Python, Flask, JavaScript, SQL, HTML, Problem Solving',
    1
);

-- Seed 15 Job Vacancies covering Graduate Students & Engineers of All Streams
INSERT INTO `jobs` (`title`, `company`, `stream`, `qualification`, `city`, `salary_min`, `salary_max`, `job_type`, `experience`, `skills_required`, `is_premium`, `is_urgent`, `is_verified`, `hr_email`, `hr_phone`, `address`, `description`) VALUES
(
    'Junior Full Stack Developer (Graduate Special)',
    'TechNova Software Labs',
    'Computer Science / IT',
    'B.Tech / B.E. / BCA / MCA / B.Sc IT',
    'Bengaluru',
    30000, 45000, 'Full Time', 'Freshers / 0-1 yr',
    'Python, Flask, JavaScript, HTML, CSS, MySQL, Git',
    1, 1, 1,
    'careers@technova.in', '+91 80 4123 9001', 'Electronic City, Bengaluru',
    'Great opportunity for Computer Science graduates to build scalable web applications, REST APIs in Flask, and interactive frontend interfaces.'
),
(
    'Graduate Engineer Trainee (GET) - CAD Design & Production',
    'Bharat Precision AutoWorks',
    'Mechanical Engineering',
    'B.Tech / B.E. Mechanical / Diploma',
    'Pune',
    25000, 38000, 'Full Time', 'Freshers / 0-1 yr',
    'AutoCAD, SolidWorks, GD&T, Production Planning, Quality Control',
    1, 1, 1,
    'hr@bharatprecision.com', '+91 20 6789 1234', 'MIDC Bhosari, Pune',
    'Direct hiring for mechanical engineering freshers. Hands-on training on 3D CAD modeling, component design, and shop floor assembly supervision.'
),
(
    'Site Project Engineer & Structural Estimation',
    'Apex Infra & Real Estate',
    'Civil Engineering',
    'B.Tech / B.E. Civil / Diploma Civil',
    'Mumbai',
    28000, 40000, 'Full Time', 'Freshers / 0-2 yrs',
    'AutoCAD Civil, Site Supervision, Bar Bending Schedule, Quantity Survey, Concrete Tech',
    1, 1, 1,
    'jobs@apexinfra.co.in', '+91 22 2845 6789', 'Andheri East, Mumbai',
    'Supervise on-site construction works, verify structural measurements, review blueprints, and ensure safety compliance on residential projects.'
),
(
    'Power Systems & Substation Maintenance Trainee',
    'VoltGrid Energy Systems',
    'Electrical Engineering',
    'B.Tech / B.E. Electrical (EEE)',
    'Hyderabad',
    26000, 36000, 'Full Time', 'Freshers / 0-1 yr',
    'Single Line Diagrams (SLD), Switchgear, Substation Ops, MATLAB, Electrical Safety',
    0, 1, 1,
    'talent@voltgrid.in', '+91 40 3344 5566', 'HITEC City, Hyderabad',
    'Assist senior electrical engineers in power distribution monitoring, substation equipment maintenance, and load calculations.'
),
(
    'Embedded Systems & IoT Firmware Associate',
    'SensorCore Electronics',
    'Electronics & Communication',
    'B.Tech / B.E. ECE / Embedded Systems',
    'Bengaluru',
    32000, 48000, 'Full Time', 'Freshers / 0-1 yr',
    'C/C++, Embedded C, Microcontrollers (ESP32/STM32), PCB Design, IoT Protocols',
    1, 1, 1,
    'recruit@sensorcore.tech', '+91 80 5566 7788', 'Whitefield, Bengaluru',
    'Develop micro-controller firmware, integrate sensor boards, and test wireless IoT smart sensor solutions for industrial clients.'
),
(
    'Junior Process Operations Engineer',
    'PetroChem Industrial Ltd',
    'Chemical Engineering',
    'B.Tech / B.E. Chemical',
    'Vadodara',
    28000, 42000, 'Full Time', 'Freshers / 0-1 yr',
    'P&ID, Mass & Energy Balance, Distillation, Process Safety, Aspen HYSYS',
    0, 0, 1,
    'recruitment@petrochemcorp.in', '+91 265 233 4455', 'GIDC Industrial Estate, Vadodara',
    'Monitor continuous chemical manufacturing lines, verify reaction parameters, conduct mass balance checks, and adhere to environmental safety norms.'
),
(
    'Associate Data Analyst & BI Trainee (Graduate)',
    'InsightEdge Analytics',
    'Computer Science / IT / Stats',
    'Any Graduate / B.Tech / B.Sc Stats / BCA',
    'Delhi NCR',
    32000, 50000, 'Full Time', 'Freshers / 0-1 yr',
    'Python, SQL, Advanced Excel, Power BI, Data Visualization, Statistics',
    1, 1, 1,
    'careers@insightedge.io', '+91 124 456 7890', 'Cyber City, Gurugram',
    'Transform raw operational data into actionable dashboards. Excellent launchpad for ambitious graduates passionate about data and metrics.'
),
(
    'Industrial Automation & Robotics Trainee',
    'RoboTech Dynamics',
    'Mechatronics / Robotics',
    'B.Tech Mechatronics / Mechanical / EEE',
    'Chennai',
    28000, 42000, 'Full Time', 'Freshers / 0-1 yr',
    'PLC Programming, SCADA, Industrial Robotics, Sensor Integration, Pneumatics',
    1, 1, 1,
    'jobs@robotechdynamics.com', '+91 44 2233 4455', 'Ambattur Industrial Estate, Chennai',
    'Hands-on deployment of automated pick-and-place robotic cells and programming PLC logic controllers for automotive assembly lines.'
),
(
    'Control Systems & Instrumentation Engineer',
    'Delta Automations',
    'Instrumentation & Control',
    'B.Tech / B.E. Instrumentation & Control',
    'Ahmedabad',
    27000, 39000, 'Full Time', 'Freshers / 0-1 yr',
    'PLC, DCS, Transmitters, Calibration, Loop Checking, Field Instrumentation',
    0, 1, 1,
    'hr@deltaautomations.com', '+91 79 4001 2233', 'Sanand Industrial Park, Ahmedabad',
    'Calibrate pressure, temperature, and flow transmitters. Perform loop checks and verify distributed control system wiring.'
),
(
    'Medical Devices Quality & Validation Associate',
    'BioHealth Lifesciences',
    'Biotechnology / Biomedical',
    'B.Tech Biotech / Biomedical / B.Pharma',
    'Hyderabad',
    24000, 35000, 'Full Time', 'Freshers / 0-1 yr',
    'ISO 13485, Biomedical Equipment, Validation Protocols, GLP/GMP, Lab Documentation',
    0, 0, 1,
    'careers@biohealthlife.com', '+91 40 6677 8899', 'Genome Valley, Hyderabad',
    'Participate in medical equipment sterilization validation, quality assurance documentation, and lab standard compliance.'
),
(
    'Junior Aerodynamics & Structural Analysis Trainee',
    'AeroWing Aerospace Labs',
    'Aerospace / Aeronautical',
    'B.Tech Aerospace / Mechanical',
    'Bengaluru',
    35000, 52000, 'Full Time', 'Freshers / 0-1 yr',
    'ANSYS, CFD, CATIA, Aerodynamic Simulation, Structural FEA',
    1, 1, 1,
    'hr@aerowinglabs.com', '+91 80 6611 2233', 'HAL Airport Road, Bengaluru',
    'Work alongside senior aerodynamicists to run CFD meshing and structural FEA simulations for UAV airframes.'
),
(
    'Environmental Health & Safety (EHS) Officer',
    'EcoSustain Solutions',
    'Environmental Engineering',
    'B.Tech Environmental / Chemical / Civil',
    'Delhi NCR',
    26000, 37000, 'Full Time', 'Freshers / 0-1 yr',
    'EHS Auditing, Water Treatment (STP/ETP), Environmental Impact Assessment, OSHA',
    0, 1, 1,
    'jobs@ecosustain.org', '+91 11 4123 5566', 'Okhla Industrial Area, New Delhi',
    'Conduct industrial plant safety audits, supervise effluent treatment plant (ETP) operations, and prepare environmental compliance reports.'
),
(
    'Graduate Business Development Associate',
    'PrimeScale Logistics & Commerce',
    'Any Graduate (All Streams)',
    'Any Graduate / B.Com / B.A. / B.Sc / BBA / B.Tech',
    'Mumbai',
    25000, 36000, 'Full Time', 'Freshers / 0-1 yr',
    'Client Relationship, MS Office, Communication, Sales Operations, Negotiation',
    1, 1, 1,
    'recruitment@primescalecorp.com', '+91 22 4111 2233', 'Bandra Kurla Complex (BKC), Mumbai',
    'Connect with B2B corporate clients, explain supply chain logistics offerings, negotiate service orders, and manage client partnerships.'
),
(
    'Junior Financial Analyst & Accounts Executive',
    'FinEdge Capital Advisors',
    'Commerce & Finance (Graduates)',
    'B.Com / BBA Finance / M.Com / Any Graduate',
    'Pune',
    24000, 35000, 'Full Time', 'Freshers / 0-1 yr',
    'Tally Prime, Financial Modeling, MS Excel, GST Filing, Accounts Reconciliation',
    0, 1, 1,
    'jobs@finedgeadvisors.in', '+91 20 4888 9900', 'Kalyani Nagar, Pune',
    'Prepare ledger entries, assist in quarterly GST returns, conduct bank reconciliations, and compile company financial summaries.'
),
(
    'Digital Marketing & Social Media Growth Specialist',
    'BrandPulse Media Hub',
    'Any Graduate / Media / BBA',
    'Any Graduate / Mass Comm / BBA / B.Tech',
    'Delhi NCR',
    22000, 34000, 'Full Time', 'Freshers / 0-1 yr',
    'SEO, Meta Ads, Google Analytics, Content Writing, Canva, Email Marketing',
    1, 1, 1,
    'careers@brandpulse.agency', '+91 120 455 6677', 'Sector 62, Noida',
    'Plan engaging social media campaigns, optimize organic search presence (SEO), design creatives, and write engaging copy for client brands.'
);
