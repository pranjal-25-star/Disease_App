from flask import Flask, render_template, request, jsonify, send_file
import io
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

app = Flask(__name__)

# --------- Diseases, Symptoms and Advice ----------
DISEASES = [
    "Malaria", "Covid-19", "Dengue", "Typhoid", "Cholera",
    "Influenza", "Chickenpox", "Measles", "Hepatitis A", "Common Cold"
]

SYMPTOMS = {
    "en": [
        "fever","headache","cough","sore throat","fatigue","chills",
        "body ache","rash","nausea","vomiting","diarrhea","loss of smell",
        "loss of taste","bleeding","abdominal pain","yellow skin",
        "runny nose","sneezing","itchy eyes","joint pain"
    ],
    "hi": [
        "बुखार","सर दर्द","खांसी","गले में खराश","थकान","सर्दी",
        "शरीर में दर्द","दाने","उल्टी","मतली","दस्त","गंध न आना",
        "स्वाद न आना","खून बहना","पेट दर्द","पीली त्वचा",
        "नाक बहना","छींक", "खुजली आंखें","जोड़ दर्द"
    ],
    "mr": [
        "ताप","डोकेदुखी","खोकला","घशाचा वेदना","थकवा","थंडी",
        "शरीरात वेदना","रॅश","उलटी","अजीर्ण","स्तूल","वास न येणे",
        "चव न येणे","रक्तस्राव","पोटदुखी","सोंडे पिवळे",
        "नाक वाहणं","हाचक","डोळ्यात खाज","सांधे वेदना"
    ]
}

DISEASE_SYMPTOMS = {
    "Malaria": ["fever","chills","headache","fatigue","body ache"],
    "Covid-19": ["fever","cough","fatigue","loss of smell","loss of taste","sore throat"],
    "Dengue": ["fever","headache","rash","joint pain","bleeding","body ache"],
    "Typhoid": ["fever","headache","abdominal pain","diarrhea","nausea"],
    "Cholera": ["diarrhea","vomiting","abdominal pain","dehydration"],
    "Influenza": ["fever","cough","sore throat","fatigue","body ache"],
    "Chickenpox": ["fever","rash","itchy eyes","fatigue"],
    "Measles": ["fever","rash","cough","runny nose","red eyes"],
    "Hepatitis A": ["fever","nausea","vomiting","yellow skin","abdominal pain"],
    "Common Cold": ["runny nose","sneezing","sore throat","cough","headache"]
}

ADVICE = {
    "Malaria": {
        "en": "See a doctor urgently. Drink fluids and get tested (blood smear/rapid test).",
        "hi": "तुरंत डॉक्टर से मिलें। तरल पदार्थ पिएं और ब्लड टेस्ट करवाएँ।",
        "mr": "तुरंत डॉक्टरकडे जा. द्रव प्या आणि रक्तचाचणी करा."
    },
    "Covid-19": {
        "en": "Isolate, test (RT-PCR/Antigen), monitor oxygen and seek care if breathing difficulty.",
        "hi": "आइसोलेट रहें, टेस्ट करवाएँ और सांस में दिक्कत होने पर तुरंत मदद लें।",
        "mr": "एकांतवास करा, टेस्ट करा आणि श्वासोच्छवास अडचण असल्यास त्वरीत वैद्यकीय मदत घ्या."
    },
    "Dengue": {
        "en": "Hydrate well, monitor platelets. Visit clinic for testing and monitoring.",
        "hi": "अच्छी तरह हाइड्रेट रहें, प्लेटलेट्स की जाँच कराएँ।",
        "mr": "पाणी भरपूर प्या, प्लेटलेट तपासा, क्लिनिकला भेट द्या."
    },
    "Typhoid": {
        "en": "Antibiotics needed after confirming diagnosis. Maintain hydration and hygiene.",
        "hi": "निदान के बाद एंटीबायोटिक लेना जरूरी है। हाइजीन और हाइड्रेशन बनाए रखें।",
        "mr": "निदानानंतर अँटीबायोटिक आवश्यक. स्वच्छता व द्रवपदार्थ ठेवा."
    },
    "Cholera": {
        "en": "Immediate rehydration therapy; seek urgent medical care.",
        "hi": "तुरंत री-हाइड्रेशन और चिकित्सा सहायता लें।",
        "mr": "त्वरीत द्रवपुनर्भरण व वैद्यकीय मदत घ्या."
    },
    "Influenza": {
        "en": "Rest, fluids, symptomatic care; antiviral if indicated.",
        "hi": "आराम करें, तरल पदार्थ पिएं, जरुरी होने पर एंटीवायरल।",
        "mr": "आलस, द्रवपदार्थ, गरजेप्रमाणे औषधं."
    },
    "Chickenpox": {
        "en": "Isolate, symptomatic care, see doctor for severe cases.",
        "hi": "आइसोलेट रहें, हल्का इलाज, गंभीर होने पर डॉक्टर दिखाएँ।",
        "mr": "एकांतवास करा, लक्षणानुसार उपचार करा, गंभीर असला तर डॉक्टरकडे जा."
    },
    "Measles": {
        "en": "Supportive care; prevent spread; see a doctor for complications.",
        "hi": "सहायक उपचार और संक्रमण से बचाव। जटिलता पर डॉक्टर दिखाएँ।",
        "mr": "साहाय्यक उपचार, फैलण्यापासून रोखा, जटिलतेसाठी डॉक्टरकडे जा."
    },
    "Hepatitis A": {
        "en": "Rest, avoid alcohol, consult doctor for liver tests and care.",
        "hi": "आराम करें, शराब से बचें और लिवर टेस्ट करवाएँ।",
        "mr": "आराम, द्राक्षारस टाळा, यकृत चाचण्या करवा."
    },
    "Common Cold": {
        "en": "Rest, fluids, symptomatic treatment (paracetamol, decongestant).",
        "hi": "आराम करें, तरल पदार्थ पिएं और लक्षणों के अनुसार दवा लें।",
        "mr": "आराम करा, द्रवपदार्थ प्या, लक्षणानुसार उपचार करा."
    }
}

# --------- State & Year-wise Data (2020-2025) for all diseases ----------
STATEWISE_YEARLY = {
    "Malaria": {
        "Maharashtra": {"2020": 450, "2021": 470, "2022": 480, "2023": 500, "2024": 520, "2025": 530},
        "UP": {"2020": 200, "2021": 210, "2022": 220, "2023": 230, "2024": 240, "2025": 250},
        "Goa": {"2020": 15, "2021": 18, "2022": 20, "2023": 22, "2024": 23, "2025": 25},
        "Karnataka": {"2020": 130, "2021": 140, "2022": 145, "2023": 150, "2024": 155, "2025": 160},
        "Madhya Pradesh": {"2020": 120, "2021": 125, "2022": 130, "2023": 135, "2024": 140, "2025": 145},
        "Punjab": {"2020": 50, "2021": 52, "2022": 55, "2023": 58, "2024": 60, "2025": 62},
        "Gujarat": {"2020": 80, "2021": 85, "2022": 90, "2023": 95, "2024": 100, "2025": 105},
        "Rajasthan": {"2020": 70, "2021": 75, "2022": 78, "2023": 80, "2024": 85, "2025": 90},
        "Assam": {"2020": 30, "2021": 32, "2022": 35, "2023": 37, "2024": 40, "2025": 42},
        "Bihar": {"2020": 60, "2021": 65, "2022": 68, "2023": 70, "2024": 72, "2025": 75},
        "Odisha": {"2020": 40, "2021": 45, "2022": 48, "2023": 50, "2024": 52, "2025": 55},
        "Uttarakhand": {"2020": 20, "2021": 22, "2022": 23, "2023": 25, "2024": 27, "2025": 30},
        "West Bengal": {"2020": 90, "2021": 95, "2022": 100, "2023": 105, "2024": 110, "2025": 115},
    },
    "Covid-19": {
        "Maharashtra": {"2020": 300, "2021": 800, "2022": 1000, "2023": 1200, "2024": 1100, "2025": 900},
        "UP": {"2020": 250, "2021": 600, "2022": 800, "2023": 900, "2024": 850, "2025": 800},
        "Goa": {"2020": 30, "2021": 60, "2022": 80, "2023": 100, "2024": 90, "2025": 80},
        "Karnataka": {"2020": 150, "2021": 400, "2022": 500, "2023": 600, "2024": 550, "2025": 500},
        "Madhya Pradesh": {"2020": 120, "2021": 300, "2022": 400, "2023": 450, "2024": 420, "2025": 400},
        "Punjab": {"2020": 50, "2021": 120, "2022": 150, "2023": 180, "2024": 170, "2025": 160},
        "Gujarat": {"2020": 80, "2021": 200, "2022": 250, "2023": 300, "2024": 280, "2025": 260},
        "Rajasthan": {"2020": 70, "2021": 180, "2022": 220, "2023": 250, "2024": 240, "2025": 230},
        "Assam": {"2020": 20, "2021": 50, "2022": 70, "2023": 80, "2024": 75, "2025": 70},
        "Bihar": {"2020": 60, "2021": 120, "2022": 150, "2023": 180, "2024": 170, "2025": 160},
        "Odisha": {"2020": 40, "2021": 80, "2022": 100, "2023": 120, "2024": 110, "2025": 100},
        "Uttarakhand": {"2020": 10, "2021": 30, "2022": 40, "2023": 50, "2024": 45, "2025": 40},
        "West Bengal": {"2020": 90, "2021": 220, "2022": 300, "2023": 350, "2024": 330, "2025": 300},
    },
    "Dengue": {
        "Maharashtra": {"2020": 600, "2021": 650, "2022": 680, "2023": 700, "2024": 720, "2025": 740},
        "UP": {"2020": 300, "2021": 320, "2022": 340, "2023": 360, "2024": 370, "2025": 380},
        "Goa": {"2020": 20, "2021": 25, "2022": 28, "2023": 30, "2024": 32, "2025": 35},
        "Karnataka": {"2020": 250, "2021": 270, "2022": 280, "2023": 300, "2024": 310, "2025": 320},
        "Madhya Pradesh": {"2020": 200, "2021": 210, "2022": 220, "2023": 230, "2024": 240, "2025": 250},
        "Punjab": {"2020": 60, "2021": 65, "2022": 70, "2023": 75, "2024": 78, "2025": 80},
        "Gujarat": {"2020": 90, "2021": 95, "2022": 100, "2023": 105, "2024": 110, "2025": 115},
        "Rajasthan": {"2020": 50, "2021": 55, "2022": 58, "2023": 60, "2024": 65, "2025": 70},
        "Assam": {"2020": 40, "2021": 45, "2022": 48, "2023": 50, "2024": 52, "2025": 55},
        "Bihar": {"2020": 70, "2021": 75, "2022": 78, "2023": 80, "2024": 82, "2025": 85},
        "Odisha": {"2020": 30, "2021": 32, "2022": 35, "2023": 38, "2024": 40, "2025": 42},
        "Uttarakhand": {"2020": 15, "2021": 18, "2022": 20, "2023": 22, "2024": 24, "2025": 25},
        "West Bengal": {"2020": 80, "2021": 85, "2022": 90, "2023": 95, "2024": 100, "2025": 105},
    },
    "Typhoid": {
        "Maharashtra": {"2020": 180, "2021": 190, "2022": 195, "2023": 200, "2024": 210, "2025": 220},
        "UP": {"2020": 100, "2021": 105, "2022": 110, "2023": 115, "2024": 120, "2025": 125},
        "Goa": {"2020": 8, "2021": 10, "2022": 12, "2023": 13, "2024": 14, "2025": 15},
        "Karnataka": {"2020": 90, "2021": 95, "2022": 100, "2023": 105, "2024": 110, "2025": 115},
        "Madhya Pradesh": {"2020": 70, "2021": 75, "2022": 78, "2023": 80, "2024": 85, "2025": 90},
        "Punjab": {"2020": 40, "2021": 42, "2022": 45, "2023": 48, "2024": 50, "2025": 52},
        "Gujarat": {"2020": 60, "2021": 65, "2022": 68, "2023": 70, "2024": 72, "2025": 75},
        "Rajasthan": {"2020": 50, "2021": 52, "2022": 55, "2023": 58, "2024": 60, "2025": 62},
        "Assam": {"2020": 25, "2021": 27, "2022": 28, "2023": 30, "2024": 32, "2025": 33},
        "Bihar": {"2020": 40, "2021": 42, "2022": 45, "2023": 48, "2024": 50, "2025": 52},
        "Odisha": {"2020": 20, "2021": 22, "2022": 25, "2023": 28, "2024": 30, "2025": 32},
        "Uttarakhand": {"2020": 10, "2021": 12, "2022": 13, "2023": 15, "2024": 17, "2025": 18},
        "West Bengal": {"2020": 45, "2021": 48, "2022": 50, "2023": 52, "2024": 55, "2025": 58},
    },
    "Cholera": {
        "Maharashtra": {"2020": 50, "2021": 52, "2022": 55, "2023": 60, "2024": 62, "2025": 65},
        "UP": {"2020": 30, "2021": 32, "2022": 35, "2023": 38, "2024": 40, "2025": 42},
        "Goa": {"2020": 3, "2021": 4, "2022": 5, "2023": 6, "2024": 6, "2025": 7},
        "Karnataka": {"2020": 20, "2021": 22, "2022": 25, "2023": 28, "2024": 30, "2025": 32},
        "Madhya Pradesh": {"2020": 18, "2021": 20, "2022": 22, "2023": 24, "2024": 25, "2025": 26},
        "Punjab": {"2020": 8, "2021": 9, "2022": 10, "2023": 11, "2024": 12, "2025": 12},
        "Gujarat": {"2020": 12, "2021": 13, "2022": 14, "2023": 15, "2024": 16, "2025": 17},
        "Rajasthan": {"2020": 10, "2021": 11, "2022": 12, "2023": 13, "2024": 14, "2025": 15},
        "Assam": {"2020": 6, "2021": 6, "2022": 7, "2023": 8, "2024": 8, "2025": 9},
        "Bihar": {"2020": 12, "2021": 12, "2022": 13, "2023": 14, "2024": 15, "2025": 16},
        "Odisha": {"2020": 5, "2021": 6, "2022": 6, "2023": 7, "2024": 8, "2025": 9},
        "Uttarakhand": {"2020": 3, "2021": 3, "2022": 4, "2023": 4, "2024": 5, "2025": 5},
        "West Bengal": {"2020": 15, "2021": 16, "2022": 17, "2023": 18, "2024": 19, "2025": 20},
    },
    "Influenza": {
        "Maharashtra": {"2020": 280, "2021": 290, "2022": 300, "2023": 310, "2024": 320, "2025": 330},
        "UP": {"2020": 150, "2021": 160, "2022": 170, "2023": 180, "2024": 190, "2025": 200},
        "Goa": {"2020": 12, "2021": 13, "2022": 14, "2023": 15, "2024": 16, "2025": 17},
        "Karnataka": {"2020": 140, "2021": 145, "2022": 150, "2023": 155, "2024": 160, "2025": 165},
        "Madhya Pradesh": {"2020": 110, "2021": 115, "2022": 120, "2023": 125, "2024": 130, "2025": 135},
        "Punjab": {"2020": 45, "2021": 48, "2022": 50, "2023": 52, "2024": 55, "2025": 58},
        "Gujarat": {"2020": 70, "2021": 75, "2022": 78, "2023": 80, "2024": 85, "2025": 88},
        "Rajasthan": {"2020": 60, "2021": 62, "2022": 65, "2023": 68, "2024": 70, "2025": 72},
        "Assam": {"2020": 25, "2021": 27, "2022": 28, "2023": 30, "2024": 32, "2025": 33},
        "Bihar": {"2020": 50, "2021": 52, "2022": 55, "2023": 58, "2024": 60, "2025": 62},
        "Odisha": {"2020": 35, "2021": 36, "2022": 38, "2023": 40, "2024": 42, "2025": 45},
        "Uttarakhand": {"2020": 18, "2021": 19, "2022": 20, "2023": 22, "2024": 23, "2025": 25},
        "West Bengal": {"2020": 75, "2021": 78, "2022": 80, "2023": 82, "2024": 85, "2025": 88},
    },
    "Chickenpox": {
    "Maharashtra": {"2020": 100, "2021": 110, "2022": 115, "2023": 120, "2024": 125, "2025": 130},
    "UP": {"2020": 60, "2021": 65, "2022": 68, "2023": 70, "2024": 72, "2025": 75},
    "Goa": {"2020": 8, "2021": 9, "2022": 10, "2023": 10, "2024": 11, "2025": 12},
    "Karnataka": {"2020": 60, "2021": 65, "2022": 68, "2023": 70, "2024": 72, "2025": 75},
    "Madhya Pradesh": {"2020": 50, "2021": 52, "2022": 55, "2023": 58, "2024": 60, "2025": 62},
    "Punjab": {"2020": 30, "2021": 32, "2022": 34, "2023": 36, "2024": 38, "2025": 40},
    "Gujarat": {"2020": 40, "2021": 42, "2022": 44, "2023": 46, "2024": 48, "2025": 50},
    "Rajasthan": {"2020": 35, "2021": 37, "2022": 38, "2023": 40, "2024": 42, "2025": 44},
    "Assam": {"2020": 20, "2021": 22, "2022": 23, "2023": 25, "2024": 26, "2025": 28},
    "Bihar": {"2020": 40, "2021": 42, "2022": 44, "2023": 46, "2024": 48, "2025": 50},
    "Odisha": {"2020": 25, "2021": 27, "2022": 28, "2023": 30, "2024": 32, "2025": 34},
    "Uttarakhand": {"2020": 12, "2021": 13, "2022": 14, "2023": 15, "2024": 16, "2025": 18},
    "West Bengal": {"2020": 45, "2021": 48, "2022": 50, "2023": 52, "2024": 55, "2025": 58},
},
"Measles": {
    "Maharashtra": {"2020": 40, "2021": 42, "2022": 45, "2023": 50, "2024": 52, "2025": 55},
    "UP": {"2020": 30, "2021": 32, "2022": 35, "2023": 38, "2024": 40, "2025": 42},
    "Goa": {"2020": 5, "2021": 6, "2022": 7, "2023": 8, "2024": 8, "2025": 9},
    "Karnataka": {"2020": 25, "2021": 28, "2022": 30, "2023": 32, "2024": 34, "2025": 36},
    "Madhya Pradesh": {"2020": 20, "2021": 22, "2022": 23, "2023": 25, "2024": 26, "2025": 28},
    "Punjab": {"2020": 10, "2021": 12, "2022": 13, "2023": 14, "2024": 15, "2025": 16},
    "Gujarat": {"2020": 15, "2021": 16, "2022": 18, "2023": 20, "2024": 21, "2025": 22},
    "Rajasthan": {"2020": 12, "2021": 14, "2022": 15, "2023": 16, "2024": 17, "2025": 18},
    "Assam": {"2020": 8, "2021": 9, "2022": 10, "2023": 11, "2024": 12, "2025": 13},
    "Bihar": {"2020": 18, "2021": 20, "2022": 22, "2023": 24, "2024": 25, "2025": 26},
    "Odisha": {"2020": 10, "2021": 12, "2022": 13, "2023": 14, "2024": 15, "2025": 16},
    "Uttarakhand": {"2020": 5, "2021": 6, "2022": 7, "2023": 8, "2024": 8, "2025": 9},
    "West Bengal": {"2020": 22, "2021": 24, "2022": 25, "2023": 26, "2024": 28, "2025": 30},
},
"Hepatitis A": {
    "Maharashtra": {"2020": 70, "2021": 75, "2022": 78, "2023": 80, "2024": 85, "2025": 90},
    "UP": {"2020": 40, "2021": 42, "2022": 45, "2023": 48, "2024": 50, "2025": 52},
    "Goa": {"2020": 5, "2021": 6, "2022": 6, "2023": 7, "2024": 7, "2025": 8},
    "Karnataka": {"2020": 35, "2021": 38, "2022": 40, "2023": 42, "2024": 45, "2025": 48},
    "Madhya Pradesh": {"2020": 30, "2021": 32, "2022": 34, "2023": 36, "2024": 38, "2025": 40},
    "Punjab": {"2020": 15, "2021": 16, "2022": 18, "2023": 19, "2024": 20, "2025": 21},
    "Gujarat": {"2020": 20, "2021": 22, "2022": 24, "2023": 25, "2024": 26, "2025": 28},
    "Rajasthan": {"2020": 18, "2021": 20, "2022": 22, "2023": 23, "2024": 24, "2025": 25},
    "Assam": {"2020": 10, "2021": 11, "2022": 12, "2023": 13, "2024": 14, "2025": 15},
    "Bihar": {"2020": 22, "2021": 23, "2022": 24, "2023": 25, "2024": 26, "2025": 27},
    "Odisha": {"2020": 12, "2021": 13, "2022": 14, "2023": 15, "2024": 16, "2025": 17},
    "Uttarakhand": {"2020": 6, "2021": 7, "2022": 7, "2023": 8, "2024": 8, "2025": 9},
    "West Bengal": {"2020": 28, "2021": 30, "2022": 32, "2023": 34, "2024": 36, "2025": 38},
},
"Common Cold": {
    "Maharashtra": {"2020": 850, "2021": 870, "2022": 880, "2023": 900, "2024": 920, "2025": 940},
    "UP": {"2020": 600, "2021": 620, "2022": 630, "2023": 650, "2024": 670, "2025": 690},
    "Goa": {"2020": 50, "2021": 55, "2022": 58, "2023": 60, "2024": 62, "2025": 65},
    "Karnataka": {"2020": 500, "2021": 520, "2022": 530, "2023": 550, "2024": 570, "2025": 590},
    "Madhya Pradesh": {"2020": 450, "2021": 470, "2022": 480, "2023": 500, "2024": 520, "2025": 540},
    "Punjab": {"2020": 200, "2021": 210, "2022": 220, "2023": 230, "2024": 240, "2025": 250},
    "Gujarat": {"2020": 300, "2021": 320, "2022": 330, "2023": 350, "2024": 370, "2025": 380},
    "Rajasthan": {"2020": 250, "2021": 260, "2022": 270, "2023": 280, "2024": 290, "2025": 300},
    "Assam": {"2020": 150,"2021": 250, "2022": 220, "2023": 260, "2024": 220, "2025": 350}

}}

# --------- Helper Functions ----------
def predict_from_symptoms(selected_symptoms, lang="en"):
    normalized = []
    if lang == "en":
        normalized = [s.lower().strip() for s in selected_symptoms]
    else:
        src_list = SYMPTOMS.get(lang, [])
        for s in selected_symptoms:
            s = s.strip()
            if s in src_list:
                idx = src_list.index(s)
                normalized.append(SYMPTOMS['en'][idx] if idx < len(SYMPTOMS['en']) else s.lower())
            else:
                normalized.append(s.lower())

    raw_scores = {}
    for disease in DISEASES:
        disease_sym = [x.lower() for x in DISEASE_SYMPTOMS.get(disease, [])]
        match_count = sum(1 for s in normalized if s in disease_sym)
        raw_scores[disease] = (match_count, len(disease_sym))

    scores = {}
    for d, (m, total) in raw_scores.items():
        scores[d] = m / total if total else 0.0

    total_score = sum(scores.values())
    if total_score == 0:
        probs = {d: 0.0 for d in DISEASES}
    else:
        probs = {d: round((scores[d] / total_score) * 100, 1) for d in DISEASES}

    matched = {}
    for d in DISEASES:
        disease_sym = [x.lower() for x in DISEASE_SYMPTOMS.get(d, [])]
        matched[d] = [s for s in normalized if s in disease_sym]

    return probs, matched

# --------- Routes ----------
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/predict")
def predict_page():
    return render_template("predict.html", diseases=DISEASES)

@app.route("/api/symptoms")
def get_symptoms():
    lang = request.args.get("lang", "en")
    return jsonify(SYMPTOMS.get(lang, SYMPTOMS["en"]))

@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.json or {}
    selected_symptoms = data.get("symptoms", [])
    lang = data.get("lang", "en")
    selected_symptoms = [s.strip() for s in selected_symptoms if s.strip()]
    probs, matched = predict_from_symptoms(selected_symptoms, lang=lang)

    # Sort by probability descending
    sorted_diseases = sorted(DISEASES, key=lambda d: probs[d], reverse=True)
    results = []
    for d in sorted_diseases:
        results.append({
            "disease": d,
            "probability": probs[d],
            "matched_symptoms": matched[d],
            "advice": ADVICE.get(d, {}).get(lang, "")
        })

    # Highest probability disease
    highest = results[0] if results else {}
    return jsonify({"results": results, "highest": highest})

@app.route("/download/pdf", methods=["POST"])
def download_pdf():
    payload = request.json or {}
    results = payload.get("results", [])
    lang = payload.get("lang", "en")

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, height-40, f"Prediction Results ({lang}) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    y = height - 70
    c.setFont("Helvetica", 11)

    for r in results:
        if y < 80:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 11)
        c.drawString(40, y, f"{r['disease']} — {r['probability']}% — Matched: {', '.join(r.get('matched_symptoms', []))}")
        y -= 16
        advice = r.get("advice","")
        for i in range(0, len(advice), 90):
            c.drawString(60, y, advice[i:i+90])
            y -= 12
        y -= 8

    buf.seek(0)
    filename = f"prediction_{lang}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    c.save()
    return send_file(buf, as_attachment=True, download_name=filename, mimetype="application/pdf")

@app.route("/stats")
def stats_page():
    return render_template("stats.html", diseases=DISEASES)

@app.route("/api/stats/data")
def api_stats():
    return jsonify({"statewise": STATEWISE_YEARLY})

# --------------------- UPDATE DATA PAGE ---------------------

@app.route("/update", methods=["GET"])
def update_page():
    """Render a page to update disease yearly data"""
    return render_template("update.html", diseases=DISEASES, states=list(next(iter(STATEWISE_YEARLY.values())).keys()), years=[str(y) for y in range(2020,2026)])

@app.route("/update_data", methods=["POST"])
def update_data_post():
    """Update the disease data from form submission"""
    disease = request.form.get("disease")
    state = request.form.get("state")
    year = request.form.get("year")
    cases = request.form.get("cases")

    try:
        cases = int(cases)
        if disease in STATEWISE_YEARLY and state in STATEWISE_YEARLY[disease] and year in STATEWISE_YEARLY[disease][state]:
            STATEWISE_YEARLY[disease][state][year] = cases
            message = f"Updated {disease} cases in {state} for {year} to {cases} ✅"
        else:
            message = "Invalid disease/state/year selection ❌"
    except:
        message = "Cases must be a number ❌"

    return render_template("update.html", diseases=DISEASES, states=list(next(iter(STATEWISE_YEARLY.values())).keys()), years=[str(y) for y in range(2020,2026)], message=message)


# --------- Run ----------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
