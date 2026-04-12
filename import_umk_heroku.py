from app import create_app, db
from app.employees.models import Employee

EMPLOYEES = [
  {
    "name": "Mrs G Mbatha",
    "jobTitle": "CAO - Corporate Affai",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr LL Aukett",
    "jobTitle": "PLMG - Plant & Logistics Manager",
    "department": "Plant",
    "heg": null
  },
  {
    "name": "Mrs SM Masinga",
    "jobTitle": "REC - Receptionist",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Miss DK Bojosi",
    "jobTitle": "PLAT - Plant Attendant",
    "department": "Plant",
    "heg": null
  },
  {
    "name": "Mr MR Ramaite",
    "jobTitle": "DCEO - COO/DEPUTY CEO",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mrs CK Sotyantya",
    "jobTitle": "SUP - Superintendent Quality and Out load",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr PJ Theron",
    "jobTitle": "FRMAN - Electrical Form",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr JB Moorcroft",
    "jobTitle": "TECHN - Technician",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mrs E Schutte",
    "jobTitle": "BUYER - Buyer",
    "department": "stores",
    "heg": null
  },
  {
    "name": "Mr PR Meruti",
    "jobTitle": "STARE - Stacker Reclaim",
    "department": "Plant",
    "heg": "Final Product-Salable stockpile, Stacker and Reclaimer"
  },
  {
    "name": "Mr BA Petrus",
    "jobTitle": "STARE - Stacker Reclaim",
    "department": "Plant",
    "heg": "Final Product-Salable stockpile, Stacker and Reclaimer"
  },
  {
    "name": "Mr TS Polelo",
    "jobTitle": "STARE - Stacker Reclaim",
    "department": "Plant",
    "heg": "Final Product-Salable stockpile, Stacker and Reclaimer"
  },
  {
    "name": "Mr OE Leabile",
    "jobTitle": "STARE - Stacker Reclaim",
    "department": "Plant",
    "heg": "Final Product-Salable stockpile, Stacker and Reclaimer"
  },
  {
    "name": "Mr H Cloete",
    "jobTitle": "BLMFR - Boilermaker Foreman",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr BD Jantjie",
    "jobTitle": "CNROP - Control Room",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr EM Dingakeng",
    "jobTitle": "CNROPP - Control Room Op",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr KN Oaths",
    "jobTitle": "STARE - Stacker Reclaim",
    "department": "Plant",
    "heg": null
  },
  {
    "name": "Mr RE Groenewaldt",
    "jobTitle": "ELECT - Electrician",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr TJ Tsotetsi",
    "jobTitle": "PITSUP - Pits Supervisor",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr MM Saku",
    "jobTitle": "RIGGE - Rigger",
    "department": "mining",
    "heg": null
  },
  {
    "name": "Mrs J Khalek",
    "jobTitle": "ASSAC - Assist Accou",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mrs DW Britz",
    "jobTitle": "PASYSU - Payroll & Syste",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr TL Selao",
    "jobTitle": "STARE - Stacker Reclaim",
    "department": "Plant",
    "heg": null
  },
  {
    "name": "Miss G Mmekwa",
    "jobTitle": "MAINP - Maintenance",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mrs M Beukes",
    "jobTitle": "CRAD - Credit Administ",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Miss LF Tegele",
    "jobTitle": "FITTE - Fitter",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr WE Sabonga",
    "jobTitle": "ELECT - Electrician",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mrs OB Bokhutleleng",
    "jobTitle": "BIDA - Business Impr & Data Anal",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mrs AS De Beer",
    "jobTitle": "HRAA - HR Access Admin",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr BG Mokwena",
    "jobTitle": "MAINPF - Maint Plan Form",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr TJ Snyman",
    "jobTitle": "ISRCC - Issue Rec Clerk",
    "department": "stores",
    "heg": null
  },
  {
    "name": "Mr IB Knight",
    "jobTitle": "DRIVE - Driver",
    "department": "stores",
    "heg": null
  },
  {
    "name": "Mr TC Hlalele",
    "jobTitle": "TECHN - Technician",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Miss N Molaolwe",
    "jobTitle": "STARE - Stacker Reclaim",
    "department": "Plant",
    "heg": null
  },
  {
    "name": "Mr TM Papasha",
    "jobTitle": "HRAD - HR Administrator",
    "department": "HR",
    "heg": null
  },
  {
    "name": "Mr WB Brikwa",
    "jobTitle": "STOMA - Storeman",
    "department": "stores",
    "heg": null
  },
  {
    "name": "Mr RT Boer",
    "jobTitle": "BOILM - Boilermaker",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr CT Love",
    "jobTitle": "SHEQ - Contractor Manager",
    "department": "Sheq",
    "heg": null
  },
  {
    "name": "Miss MM Rapoo",
    "jobTitle": "ADMAS - Admin Assist",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr MD Van Thiel Berghuys",
    "jobTitle": "SNLM - Senior Port Logistics Manager",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Miss BC Loabile",
    "jobTitle": "MAINC - Maintenance Clerk",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Miss BM Lekgetho",
    "jobTitle": "PLAT - Plant Attendant",
    "department": "Plant",
    "heg": "Final Product-Salable stockpile, Stacker and Reclaimer"
  },
  {
    "name": "Miss BL Ntehelang",
    "jobTitle": "STARE - Stacker Reclaim",
    "department": "Plant",
    "heg": "Final Product-Salable stockpile, Stacker and Reclaimer"
  },
  {
    "name": "Mr LH Olyn",
    "jobTitle": "STARE - Stacker Reclaim",
    "department": "Plant",
    "heg": "Final Product-Salable stockpile, Stacker and Reclaimer"
  },
  {
    "name": "Mr TC Mosimanetau",
    "jobTitle": "ELECT - Electrician",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Ms A Rosi",
    "jobTitle": "SHSPP - Shift Supervisor - Process Plant",
    "department": "Plant",
    "heg": null
  },
  {
    "name": "Ms NG Liphalane",
    "jobTitle": "COMO - Comm Officer",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr SMM Nchoe",
    "jobTitle": "SHSPP - Shift Supervisor - Process Plant",
    "department": "Plant",
    "heg": null
  },
  {
    "name": "Mr NA Nyaku",
    "jobTitle": "STARE - Stacker Reclaim",
    "department": "Plant",
    "heg": "Final Product-Salable stockpile, Stacker and Reclaimer"
  },
  {
    "name": "Mr LE Makukumare",
    "jobTitle": "EMEF - EME Eng Foreman",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr LS Mokoena",
    "jobTitle": "CNROP - Control Room",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr NEM Mahatalle",
    "jobTitle": "CNROP - Control Room",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr WC Du Plessis",
    "jobTitle": "SUPFIT - Supervisor Fitting",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr T Pharasi",
    "jobTitle": "OQOL - Off Qua&Out",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr BH Van Tonder",
    "jobTitle": "BUYER - Buyer",
    "department": "stores",
    "heg": null
  },
  {
    "name": "Mr PD Magare",
    "jobTitle": "STARE - Stacker Reclaim",
    "department": "Plant",
    "heg": "Final Product-Salable stockpile, Stacker and Reclaimer"
  },
  {
    "name": "Mr BM Bosman",
    "jobTitle": "CNROPP - Control Room Op",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Miss KA Morwe",
    "jobTitle": "STARE - Stacker Reclaim",
    "department": "Plant",
    "heg": null
  },
  {
    "name": "Mr TG Modise",
    "jobTitle": "SHSPP - Shift Supervisor - Process Plant",
    "department": "Plant",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr KP Kurite",
    "jobTitle": "STARE - Stacker Reclaim",
    "department": "Plant",
    "heg": "Final Product-Salable stockpile, Stacker and Reclaimer"
  },
  {
    "name": "Mrs KS Seothaeng",
    "jobTitle": "CNROPP - Control Room Op",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr MG Ramoroka",
    "jobTitle": "PPSUP - Superintendent",
    "department": "Plant",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr LL Van Niekerk",
    "jobTitle": "ELECT - Electrician",
    "department": "Engineering",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr BP Botha",
    "jobTitle": "RIKOF - Risk Officer",
    "department": "Sheq",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr TT Itumeleng",
    "jobTitle": "STARE - Stacker Reclaim",
    "department": "Plant",
    "heg": "Final Product-Salable stockpile, Stacker and Reclaimer"
  },
  {
    "name": "Miss SI Segole",
    "jobTitle": "CNROPP - Control Room Op",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Ms ET Mvimbi",
    "jobTitle": "SHSPP - Shift Supervisor - Process Plant",
    "department": "Plant",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr JK Ntho",
    "jobTitle": "SERFT - Servicemen F",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Ms L Spanneberg",
    "jobTitle": "OHPRA - OH Practitio",
    "department": "Clinic",
    "heg": null
  },
  {
    "name": "Mr OG Leshope",
    "jobTitle": "SAFOF - Safety Officer",
    "department": "SD",
    "heg": null
  },
  {
    "name": "Mr RA Makhene",
    "jobTitle": "HRDP - HRD Practitioner",
    "department": "HR",
    "heg": null
  },
  {
    "name": "Mr D Uys",
    "jobTitle": "FITTE - Fitter",
    "department": "Engineering",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Miss N Maistry",
    "jobTitle": "FINMAA - Financial & Man",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr T Jackals",
    "jobTitle": "FITTE - Fitter",
    "department": "Engineering",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr ED Conga",
    "jobTitle": "BOILM - Boilermaker",
    "department": "Engineering",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr T Motlatsi",
    "jobTitle": "DIEME - Diesel Mechanic",
    "department": "Engineering",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr GT Obuseng",
    "jobTitle": "ISRCC - Issue Rec Clerk",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr L Selobile",
    "jobTitle": "PLAT - Plant Attendant",
    "department": "Plant",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr IM Foromane",
    "jobTitle": "RIGGE - Rigger",
    "department": "Engineering",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr MP Ramoshaba",
    "jobTitle": "FITTE - Fitter",
    "department": "Engineering",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr EP Roberts",
    "jobTitle": "ELECT - Electrician",
    "department": "Engineering",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Ms LM Bosiamang",
    "jobTitle": "PLAT - Plant Attendant",
    "department": "Plant",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr AJ Van Der Westhuizen",
    "jobTitle": "PLAT - Plant Attendant",
    "department": "Plant",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr OI Gaboutlwelwe",
    "jobTitle": "STARE - Stacker Reclaim",
    "department": "Plant",
    "heg": "Final Product-Salable stockpile, Stacker and Reclaimer"
  },
  {
    "name": "Mr TR Seimelo",
    "jobTitle": "SSOFF - Snr Safety O",
    "department": "SD",
    "heg": null
  },
  {
    "name": "Mr AT Mokoena",
    "jobTitle": "PRENG - Project Engineer",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr PJA Loots",
    "jobTitle": "BOILM - Boilermaker",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr ME Molore",
    "jobTitle": "HRAD - HR Administrator",
    "department": "HR",
    "heg": null
  },
  {
    "name": "Mr T Mudau",
    "jobTitle": "ENVOF - Environmenta",
    "department": "SD",
    "heg": null
  },
  {
    "name": "Miss YL Kailane",
    "jobTitle": "MAINC - Maintenance Clerk",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr D Gordine",
    "jobTitle": "CTO - Chief Technical",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mrs A van Niekerk",
    "jobTitle": "CFO - Chief Financial",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr LP Zenzwa",
    "jobTitle": "STARE - Stacker Reclaim",
    "department": "Plant",
    "heg": null
  },
  {
    "name": "Mr PG Seikaneng",
    "jobTitle": "STROF - Senior Training",
    "department": "HR",
    "heg": null
  },
  {
    "name": "Mr G Lingen",
    "jobTitle": "CNROP - Control Room",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr MI Matlhoko",
    "jobTitle": "ADMS - Administrative Assistant",
    "department": "HR",
    "heg": null
  },
  {
    "name": "Mr ME Moshidi",
    "jobTitle": "BLTSA - Belt Splicer As",
    "department": "Engineering",
    "heg": "Final Product-Salable stockpile, Stacker and Reclaimer"
  },
  {
    "name": "Mr JB Ngobeni",
    "jobTitle": "BLTS - Belt Splicer",
    "department": "Engineering",
    "heg": "Final Product-Salable stockpile, Stacker and Reclaimer"
  },
  {
    "name": "Mr TA Dikwidi",
    "jobTitle": "BLTS - Belt Splicer",
    "department": "Engineering",
    "heg": "Final Product-Salable stockpile, Stacker and Reclaimer"
  },
  {
    "name": "Mr TA Orapeleng",
    "jobTitle": "BLTSA - Belt Splicer As",
    "department": "Engineering",
    "heg": "Final Product-Salable stockpile, Stacker and Reclaimer"
  },
  {
    "name": "Mr MO Phayane",
    "jobTitle": "CLCO - Chief Legal & Compliance Officer",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr JJ Spangenberg",
    "jobTitle": "ENGMN - Engineer Manager",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr OP Lanka",
    "jobTitle": "PLAT - Plant Attendant",
    "department": "Plant",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr HH Neels",
    "jobTitle": "PLMB - Plumber",
    "department": "Engineering",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr K Buffel",
    "jobTitle": "HRDP - HRD Practitioner",
    "department": "HR",
    "heg": null
  },
  {
    "name": "Mr KG Maseko",
    "jobTitle": "OQOL - Off Qua&Out",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr BR Diegaardt",
    "jobTitle": "STS - Supervisor Stores",
    "department": "stores",
    "heg": null
  },
  {
    "name": "Mr T Totong",
    "jobTitle": "SASP - Safety Superintendent",
    "department": "SD",
    "heg": null
  },
  {
    "name": "Ms RL Uithaler",
    "jobTitle": "CRECL - Creditors Clerk",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr KD Malepane",
    "jobTitle": "GEOLG - Geologist",
    "department": "Technical Services",
    "heg": null
  },
  {
    "name": "Mr MG Curror",
    "jobTitle": "CEO - CEO",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr N Mothibedi",
    "jobTitle": "ISRCC - Issue Rec Clerk",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr KP Kalamore",
    "jobTitle": "DIEME - Diesel Mechanic",
    "department": "Engineering",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr GS Snyders",
    "jobTitle": "DIEME - Diesel Mechanic",
    "department": "Engineering",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr JFC Bruwer",
    "jobTitle": "DIEME - Diesel Mechanic",
    "department": "Engineering",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr LM Kuriti",
    "jobTitle": "DIEME - Diesel Mechanic",
    "department": "Engineering",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr OJ Pretorius",
    "jobTitle": "SUMP - Superintendent",
    "department": "Plant",
    "heg": null
  },
  {
    "name": "Mr FJ Van Tonder",
    "jobTitle": "DIEME - Diesel Mechanic",
    "department": "Engineering",
    "heg": "Surface Workshop- Engineering structure"
  },
  {
    "name": "Mr RJ Seretse",
    "jobTitle": "CRECL - Creditors Clerk",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr MT Mamabolo",
    "jobTitle": "ESDMAN - ESD Manager",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mrs ZP Kunene",
    "jobTitle": "PROMAN - Procurement Manager",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr BH Letsholo",
    "jobTitle": "BOILM - Boilermaker",
    "department": "Engineering",
    "heg": "Surface Workshop- Engineering structure"
  },
  {
    "name": "Ms KM Mogolegeng",
    "jobTitle": "ELECT - Electrician",
    "department": "Engineering",
    "heg": "Surface Workshop- Engineering structure"
  },
  {
    "name": "Mrs MA Mzazi",
    "jobTitle": "SHSP - Shift Superviso",
    "department": "Engineering",
    "heg": "Surface Workshop- Engineering structure"
  },
  {
    "name": "Mr SM Khamali",
    "jobTitle": "SHSP - Shift Superviso",
    "department": "Engineering",
    "heg": "Surface Workshop- Engineering structure"
  },
  {
    "name": "Mr KV Moeng",
    "jobTitle": "SHSP - Shift Superviso",
    "department": "Engineering",
    "heg": "Surface Workshop- Engineering structure"
  },
  {
    "name": "Mr TV Gonkgang",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr S Lepedi",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr KC Matong",
    "jobTitle": "CNROPL - Control Room Opertor",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr AV Thebeyagae",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr NM Lekgoe",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr PF Modisaemang",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr G Koago",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr K Leepile",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr C Poha",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr MC Mabebe",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr DP Nthekang",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr R Novela",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr GN Gwate",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr TAL Kurite",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr A Vries",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr LD Mmereki",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr TF Oss",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr O Tikane",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr JJ Tshipagaebonwe",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr MJ Koromendu",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr OV Mohapanele",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr TM Tsogang",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr BR Ramotsongwa",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mrs TC Thekoeng",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Miss KC Madito",
    "jobTitle": "CNROPL - Control Room Opertor",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr LR Boihang",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr TK Baikai",
    "jobTitle": "PLAT - Plant Attendant",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr KE Seimelo",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr TK Thobega",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr PS Tholo",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr S Molongwane",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr WW Moremi",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr PB Mosimane",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr LT Pule",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr NR Foromane",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr BI Sebuasengwe",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr M Kgosinyane",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Ms TM Ntaolang",
    "jobTitle": "PLAT - Plant Attendant",
    "department": "Plant",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mrs KP Lekhobe",
    "jobTitle": "CNROPL - Control Room Opertor",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr GE Boikanyo",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr BG Moitse",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr KM Gaethijwe",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr N Mocwana",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr KJ Mocumi",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr NI Leberegane",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr TA Hikwane",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr OI Kilelo",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr LV Otsokwa",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr MP Motlhaolwa",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Miss PT Gasebonwe",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr KV Motlele",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr NA Moatlhodi",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr OG Gatisang",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr MJ Molapisi",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr ME Dithobe",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr GJ Galeboe",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr GP Mofokeng",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr LH Taukobong",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr MT Moilwe",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr OE Hane",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Ms NI Oliphant",
    "jobTitle": "CNROPL - Control Room Opertor",
    "department": "Unknown",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr W Makudubele",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr BK Mokoto",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr OS Balibi",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr PC Sehako",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr ML Sebolai",
    "jobTitle": "TMMO - TMM Operators",
    "department": "Plant",
    "heg": "Opencast Trackless Mobile Machines Operations-Load and Haul"
  },
  {
    "name": "Mr SH Joanessa",
    "jobTitle": "MILLW - Millwrite",
    "department": "Engineering",
    "heg": "Surface Workshop- Engineering structure"
  },
  {
    "name": "Ms A Liebenberg",
    "jobTitle": "HRADM - HRD Admininistrator",
    "department": "hr",
    "heg": null
  },
  {
    "name": "Mr LS Mdala",
    "jobTitle": "PITSUP - Pits Supervisor",
    "department": "Mining",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr G Hartman",
    "jobTitle": "REFTEC - Refridgeration",
    "department": "Engineering",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Ms TA Mashwama",
    "jobTitle": "DIEME - Diesel Mechanic",
    "department": "Engineering",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mrs PR Matshediso",
    "jobTitle": "SHSP - Shift Superviso",
    "department": "Plant",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Miss BJ Rapelang",
    "jobTitle": "LA - Learner Artisan",
    "department": "Engineering",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr PM Neko",
    "jobTitle": "SURVY - Surveyor",
    "department": "Technical Services",
    "heg": null
  },
  {
    "name": "Ms B Rapoo",
    "jobTitle": "ADMS - Administrative Assistant",
    "department": "Admin",
    "heg": null
  },
  {
    "name": "Ms DKB Maboe",
    "jobTitle": "LA - Learner Artisan",
    "department": "Engineering",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr ME Mocwane",
    "jobTitle": "LA - Learner Artisan",
    "department": "Engineering",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr PR Naidoo",
    "jobTitle": "SSA - SNR Solutions A",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mrs NR Shika",
    "jobTitle": "HRMAN - HR Manager",
    "department": "hr",
    "heg": null
  },
  {
    "name": "Mrs G Pule",
    "jobTitle": "HRSUP - HRD Superint",
    "department": "hr",
    "heg": null
  },
  {
    "name": "Mrs S Wagner",
    "jobTitle": "PAYOF - Payrol Officer",
    "department": "Admin",
    "heg": null
  },
  {
    "name": "Mr L Kgatlhane",
    "jobTitle": "PLAT - Plant Attendant",
    "department": "Plant",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr M Seate",
    "jobTitle": "PLAT - Plant Attendant",
    "department": "Plant",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr JL Chipanga",
    "jobTitle": "PLAT - Plant Attendant",
    "department": "Plant",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr MJA Mosupyoe",
    "jobTitle": "GM - General Manager",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mrs NM Van Rensburg",
    "jobTitle": "PHCN - Primary Health",
    "department": "Clinic",
    "heg": null
  },
  {
    "name": "Mr CR Roman",
    "jobTitle": "LA - Learner Artisan",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr P Tau",
    "jobTitle": "LA - Learner Artisan",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Miss KA Hendrick",
    "jobTitle": "LA - Learner Artisan",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr KT Tau",
    "jobTitle": "LA - Learner Artisan",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Miss T Kgokong",
    "jobTitle": "LA - Learner Artisan",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr TG Gaseutlwiwe",
    "jobTitle": "LA - Learner Artisan",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr BQ Phetane",
    "jobTitle": "LA - Learner Artisan",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr KG Mohutsiwa",
    "jobTitle": "LA - Learner Artisan",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Miss OG Phiti",
    "jobTitle": "LA - Learner Artisan",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Miss BC Monese",
    "jobTitle": "APDM - App Diesel Mech",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Miss KR Diemeng",
    "jobTitle": "LA - Learner Artisan",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr KS Chere",
    "jobTitle": "APDM - App Diesel Mech",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Miss T Seatlhodi",
    "jobTitle": "LA - Learner Artisan",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Miss N Mazula",
    "jobTitle": "IGL - Internship Geology",
    "department": "Technical Services",
    "heg": null
  },
  {
    "name": "Miss TW Luthuli",
    "jobTitle": "ISRCC - Issue Rec Clerk",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mrs A Gribble",
    "jobTitle": "JRMAP - Junior Maintena",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr T Moetlo",
    "jobTitle": "OQOL - Off Qua&Out",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr OF Marumo",
    "jobTitle": "ELECT - Electrician",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr PJ Khonou",
    "jobTitle": "PLAT - Plant Attendant",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mrs T Magare",
    "jobTitle": "ADMCL - Admin Clerk",
    "department": "Plant",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr BG Diphakedi",
    "jobTitle": "PLAT - Plant Attendant",
    "department": "Plant",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr P Gaosenkwe",
    "jobTitle": "PLAT - Plant Attendant",
    "department": "Plant",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr OA Katong",
    "jobTitle": "PLAT - Plant Attendant",
    "department": "Plant",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr KB Tsele",
    "jobTitle": "LA - Learner Artisan",
    "department": "Plant",
    "heg": "Roving Plant Fixed plants"
  },
  {
    "name": "Mr RR Itumeleng",
    "jobTitle": "SSOFF - Snr Safety O",
    "department": "SD",
    "heg": null
  },
  {
    "name": "Mr SS Ngomane",
    "jobTitle": "HRSUP - HRD Superint",
    "department": "HR",
    "heg": null
  },
  {
    "name": "Mr MK Minnaar",
    "jobTitle": "STORESS - Stores Superintendent",
    "department": "stores",
    "heg": null
  },
  {
    "name": "Mr PJ Venter",
    "jobTitle": "TECMA - Technical Manag",
    "department": "Technical Services",
    "heg": null
  },
  {
    "name": "Miss B Mohapi",
    "jobTitle": "APPL - Apprentice Boil",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr TR Jogom",
    "jobTitle": "APDM - App Diesel Mech",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr C Bodumele",
    "jobTitle": "PITSUP - Pits Supervisor",
    "department": "Plant",
    "heg": null
  },
  {
    "name": "Mrs D Gangaram",
    "jobTitle": "FINMAA - Financial & Man",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Miss BJ Ferris",
    "jobTitle": "SYSSA - Systems Adminstrator",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Miss AM Kwinda",
    "jobTitle": "ESGA - EG Adminstrator",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr JF Nel",
    "jobTitle": "ELECT - Electrician",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr K Mohatlhe",
    "jobTitle": "APEL - Apprentice Elec",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr TS Otswelang",
    "jobTitle": "BOILM - Boilermaker",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mrs AQ Quluba",
    "jobTitle": "JNRACC - Junior Accountant",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr ET Matlapeng",
    "jobTitle": "SDM - Sustainable Development Manager",
    "department": "SD",
    "heg": null
  },
  {
    "name": "Mr Z Masuku",
    "jobTitle": "BOILM - Boilermaker",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr N Sedilang",
    "jobTitle": "ELECT - Electrician",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr RI Majoro",
    "jobTitle": "FITTE - Fitter",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Miss LM Mmotla",
    "jobTitle": "IME - Internship Mech",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Ms S Singh",
    "jobTitle": "JNRACC - Junior Accountant",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr JJ Van Zyl",
    "jobTitle": "STROF - Senior Training",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr BC Mnguni",
    "jobTitle": "SNIAD&SP - Snr Int Auditor & Special Projects",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr N Bapoo",
    "jobTitle": "CCLO - CHIEF COMMERCIA",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr LO Esikang",
    "jobTitle": "INTMP - Internship Mine Planning",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Ms KR Mochoge",
    "jobTitle": "INGT - Intership Geo Technical",
    "department": "Unknown",
    "heg": null
  },
  {
    "name": "Mr G Megalanyane",
    "jobTitle": "APPL - Apprentice Boil",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Ms A Mmudi",
    "jobTitle": "MPL - Min Proc Learns",
    "department": "Plant",
    "heg": null
  },
  {
    "name": "Mr TT Motlhabane",
    "jobTitle": "MPL - Min Proc Learns",
    "department": "Plant",
    "heg": null
  },
  {
    "name": "Mr KB Mathobo",
    "jobTitle": "APFT - Apprentice Fit",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr JR Bock",
    "jobTitle": "APPL - Apprentice Boil",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Ms BA Tagane",
    "jobTitle": "MPL - Min Proc Learns",
    "department": "Plant",
    "heg": null
  },
  {
    "name": "Mrs KC Applegreen",
    "jobTitle": "APFT - Apprentice Fit",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Mr PR Radingwana",
    "jobTitle": "PLENG - Plant Engineer",
    "department": "Engineering",
    "heg": null
  },
  {
    "name": "Ms MF Thupae",
    "jobTitle": "MLS - Mining Learners",
    "department": "Mining",
    "heg": null
  },
  {
    "name": "Miss JZB Booysen",
    "jobTitle": "MLS - Mining Learners",
    "department": "Mining",
    "heg": null
  },
  {
    "name": "Ms N Mosiapoa",
    "jobTitle": "MLS - Mining Learners",
    "department": "Mining",
    "heg": null
  },
  {
    "name": "Mr N Sesing",
    "jobTitle": "MLS - Mining Learners",
    "department": "Mining",
    "heg": null
  },
  {
    "name": "Mr T Moruakgomo",
    "jobTitle": "MLS - Mining Learners",
    "department": "Mining",
    "heg": null
  },
  {
    "name": "Ms DL Majeng",
    "jobTitle": "MLS - Mining Learners",
    "department": "Mining",
    "heg": null
  },
  {
    "name": "Mr TP Matong",
    "jobTitle": "MLS - Mining Learners",
    "department": "Mining",
    "heg": null
  },
  {
    "name": "Mr KA Galokaiwe",
    "jobTitle": "MLS - Mining Learners",
    "department": "Mining",
    "heg": null
  },
  {
    "name": "Mr TF Sebati",
    "jobTitle": "MLS - Mining Learners",
    "department": "Mining",
    "heg": null
  },
  {
    "name": "Mr KD Baganeneng",
    "jobTitle": "MLS - Mining Learners",
    "department": "Mining",
    "heg": null
  },
  {
    "name": "Mr MO Belang",
    "jobTitle": "MLS - Mining Learners",
    "department": "Mining",
    "heg": null
  },
  {
    "name": "Miss TE Phang",
    "jobTitle": "MLS - Mining Learners",
    "department": "Mining",
    "heg": null
  },
  {
    "name": "Miss KP Difolokwe",
    "jobTitle": "MLS - Mining Learners",
    "department": "Mining",
    "heg": null
  },
  {
    "name": "Ms T Olyn",
    "jobTitle": "MLS - Mining Learners",
    "department": "Mining",
    "heg": null
  },
  {
    "name": "Miss RN Mnanzana",
    "jobTitle": "INCM - Intern Commerci",
    "department": "stores",
    "heg": null
  },
  {
    "name": "Mr K Mababo",
    "jobTitle": "SENG - Service Engineer",
    "department": "Plant",
    "heg": null
  },
  {
    "name": "Miss TA Marwane",
    "jobTitle": "MLS - Mining Learners",
    "department": "Mining",
    "heg": null
  },
  {
    "name": "Mr TC Chakane",
    "jobTitle": "MLS - Mining Learners",
    "department": "Mining",
    "heg": null
  },
  {
    "name": "Mr T Kiet",
    "jobTitle": "MLS - Mining Learners",
    "department": "Mining",
    "heg": null
  },
  {
    "name": "Miss F Liebenberg",
    "jobTitle": "MPL - Min Proc Learns",
    "department": "Plant",
    "heg": null
  },
  {
    "name": "Mrs TJ Mazibuko",
    "jobTitle": "TCOMO - Temp Communications & Office Admin",
    "department": "Admin",
    "heg": null
  },
  {
    "name": "Mr MG Nelufule",
    "jobTitle": "ROCENG - Rock Engineer",
    "department": "Technical Services",
    "heg": null
  },
  {
    "name": "Mr M Morometse",
    "jobTitle": "HRP - HR Practitioner",
    "department": "HR",
    "heg": null
  },
  {
    "name": "Mr ZV Hlongwane",
    "jobTitle": "HRP - HR Practitioner",
    "department": "HR",
    "heg": null
  }
]

app = create_app()
with app.app_context():
    existing = {e.name.lower() for e in Employee.query.all()}
    added = 0
    for d in EMPLOYEES:
        if d["name"].lower() in existing:
            continue
        emp = Employee(
            name       = d["name"],
            job_title  = d["jobTitle"],
            department = d["department"],
            heg_number = d["heg"],
            is_active  = True,
        )
        db.session.add(emp)
        added += 1
    db.session.commit()
    print(f"Done — {added} employees imported.")
