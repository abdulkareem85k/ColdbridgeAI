/**
 * ColdBridge AI - Localization Dictionary (i18n)
 * Supports English (en), Hindi (hi), and Marathi (mr).
 * English is the default.
 * Note: Non-English machine-written translations are marked "needs native-speaker review".
 */

export const translations = {
    en: {
        brand_title: "❄️ ColdBridge AI",
        farmer_portal: "Farmer Portal",
        nav_overview: "Overview",
        nav_add_produce: "Add Produce",
        nav_cooling_map: "Cooling Map",
        nav_batches: "My Batches & SRI",
        nav_matches: "Cooling Matches",
        nav_bookings: "My Bookings",
        logout: "Logout",
        overview_title: "Farmer Overview",
        overview_subtitle: "Track your registered harvest batches, spoilage risk assessments, and cold chain options.",
        stat_batches: "📦 Total Batches",
        stat_produce: "⚖️ Total Produce",
        stat_high_risk: "🚨 High Risk Batches",
        recent_batches_title: "Recent Batches & Spoilage Assessments",
        refresh: "Refresh",
        register_title: "Register New Produce Batch",
        register_subtitle: "Record field ambient conditions and get an instant transparent Spoilage Risk Index (SRI).",
        crop_label: "Produce Crop *",
        quantity_label: "Harvest Quantity (kg) *",
        harvest_time_label: "Harvest Timestamp *",
        ambient_temp_label: "Field Ambient Temp (°C) *",
        location_label: "Farmgate Location (OpenStreetMap Picker) *",
        notes_label: "Batch Notes & Observations",
        btn_register_sri: "Register Batch & Calculate SRI",
        sri_title: "Spoilage Risk Index (SRI)",
        sri_honesty: "Rule-based prototype estimate (not scientifically validated spoilage prediction)",
        urgency_low: "Low Urgency",
        urgency_medium: "Moderate Urgency",
        urgency_high: "Critical Urgency (High Spoilage Risk)",
        cooling_matches_title: "Cooling Infrastructure Allocation",
        cooling_matches_subtitle: "Reverse-auction scoring across static cold rooms and mobile solar cooling vans.",
        btn_find_match: "Find Cold Chain Match",
        btn_accept_offer: "Accept & Reserve Capacity",
        btn_cancel_booking: "Cancel Booking",
        data_source_simulated: "DATA SOURCE: SIMULATED",
        data_status_fresh: "DATA STATUS: FRESH",
        solar_simulation_notice: "Degraded-Solar Fallback: Simplified simulation (effective capacity = available capacity × solar reliability). Hardware sensors belong to later phase.",
        crop_mango: "Mango (Kesar / Alphonso)",
        crop_tomato: "Tomato",
        crop_grapes: "Grapes",
        crop_onion: "Onion",
        crop_strawberry: "Strawberry",
        crop_pomegranate: "Pomegranate",
        crop_cashew_apple: "Cashew Apple",

        // Index / Auth
        auth_welcome: "Welcome to ColdBridge AI",
        auth_subtitle: "Pay-per-use cold chain logistics & smart cross-asset matching",
        tab_sign_in: "Sign In",
        tab_register: "Register",
        label_email: "Email Address",
        label_password: "Password",
        btn_sign_in: "Sign In",
        demo_logins_title: "Quick Demo Logins (Maharashtra Demo Dataset):",
        label_full_name: "Full Name",
        label_phone: "Phone Number",
        label_role: "I want to register as:",
        btn_create_account: "Create Account",

        // Operator Portal
        operator_portal: "Operator Portal",
        nav_my_assets: "My Assets",
        nav_active_bookings: "Active Bookings",
        nav_surplus_inv: "Surplus & Inventory",
        nav_utilization: "Capacity Utilization",
        nav_sri_queue: "SRI Priority Queue",
        nav_add_static: "Add Cold Room",
        nav_add_van: "Add Solar Van",
        fleet_title: "Cooling Infrastructure Fleet",
        fleet_subtitle: "Manage your registered static cold rooms and mobile solar cooling vans.",
        btn_refresh: "Refresh",

        // Buyer Portal
        buyer_portal: "Buyer Portal",
        nav_surplus_market: "Surplus Marketplace",
        nav_my_orders: "My Orders",
        nav_demand_forecasts: "Demand Forecasts",
        surplus_market_title: "Near-Expiry Surplus Marketplace",
        surplus_market_subtitle: "Procure farm-fresh pre-cooled produce at sliding discounts certified by facility operators.",

        // Admin Portal
        admin_portal: "System Admin",
        nav_system_overview: "System Overview",
        nav_simulation_controls: "Simulation Controls",
        nav_audit_trail: "Audit Trail",
        admin_title: "Platform Operations Dashboard",
        admin_subtitle: "System health, infrastructure counts, and active cold-chain allocations.",

        // Part 5 E2: Farmer Asset Type Clarity & Filter Keys
        type_storage_room: "Storage Room",
        type_solar_van: "Solar Van",
        storage_delivery_note: "You deliver your produce to this facility.",
        van_pickup_note: "This van comes to your farm to pick up.",
        filter_all_types: "All Options",
        filter_storage_only: "Storage Rooms",
        filter_vans_only: "Solar Vans",
        no_solar_van_in_range: "No solar van available within range",
        no_storage_room_in_range: "No storage room available within range",
        label_service_radius: "Service Radius",
        label_pickup_eta: "Pickup ETA",
        label_effective_capacity: "Effective Capacity",
        label_simulated: "Simulated",
        label_supported_crops: "Supported Crops",
        label_temp_range: "Temp Range",
        label_daily_rate: "Rate per day",

        // Part 4 D2: Public Directory Keys
        dir_card_title: "Public Cold Storage Directory – Nashik and Pune",
        dir_judge_statement: "These are real cold storage facilities in Nashik and Pune, taken from public directories. A farmer can contact them directly. The ranking and bids in our prototype are still simulated.",
        dir_filter_district: "District Filter",
        dir_filter_all: "All Districts",
        dir_filter_nashik: "Nashik",
        dir_filter_pune: "Pune",
        dir_search_placeholder: "Search by facility name, area, or address...",
        dir_btn_search: "Search",
        dir_badge_public: "PUBLIC LISTING",
        dir_badge_not_partner: "NOT A COLDBRIDGE PARTNER",
        dir_btn_call: "Call",
        dir_btn_copy_phone: "Copy Number",
        dir_btn_show_map: "Show on Map",
        dir_unverified_warning: "Unverified – call to confirm",
        dir_no_phone: "No phone listed",
        dir_loading: "Loading directory listings...",
        dir_empty: "No public cold storage facilities found matching your criteria.",
        dir_error: "Unable to load public directory listings. Please try again later.",
        dir_copied_alert: "Phone number copied to clipboard!"
    },
    hi: {
        brand_title: "❄️ कोल्डब्रिज एआई",
        farmer_portal: "किसान पोर्टल",
        nav_overview: "अवलोकन",
        nav_add_produce: "फसल जोड़ें",
        nav_cooling_map: "कोल्ड स्टोरेज मैप",
        nav_batches: "मेरी फसलें व SRI",
        nav_matches: "कोल्ड चेन विकल्प",
        nav_bookings: "मेरी बुकिंग",
        logout: "लॉग आउट",
        overview_title: "किसान अवलोकन",
        overview_subtitle: "अपनी पंजीकृत फसल, खराबी जोखिम सूचकांक (SRI) और कोल्ड चेन विकल्पों को ट्रैक करें।",
        stat_batches: "📦 कुल फसलें",
        stat_produce: "⚖️ कुल उत्पादन",
        stat_high_risk: "🚨 उच्च जोखिम वाली फसलें",
        recent_batches_title: "हालिया फसलें और खराब होने का जोखिम",
        refresh: "ताज़ा करें",
        register_title: "नई फसल पंजीकृत करें",
        register_subtitle: "खेत के तापमान की स्थिति दर्ज करें और तुरंत पारदर्शी स्पॉइलेज रिस्क इंडेक्स (SRI) प्राप्त करें।",
        crop_label: "फसल का प्रकार *",
        quantity_label: "फसल मात्रा (किग्रा) *",
        harvest_time_label: "कटाई का समय *",
        ambient_temp_label: "खेत का तापमान (°C) *",
        location_label: "खेत का स्थान (ओपनस्ट्रीटमॅप चयनकर्ता) *",
        notes_label: "फसल विवरण व गुणवत्ता टिप्पणी",
        btn_register_sri: "फसल दर्ज करें व SRI गणना करें",
        sri_title: "स्पॉइलेज रिस्क इंडेक्स (SRI)",
        sri_honesty: "पारदर्शी नियम-आधारित प्रोटोटाइप अनुमान (वैज्ञानिक रूप से प्रमाणित समय भविष्यवाणी नहीं)",
        urgency_low: "कम जोखिम",
        urgency_medium: "मध्यम जोखिम",
        urgency_high: "गंभीर जोखिम (तत्काल कूलिंग आवश्यक)",
        cooling_matches_title: "कोल्ड स्टोरेज और सोलर वैन आवंटन",
        cooling_matches_subtitle: "स्थिर शीतगृहों और सौर मोबाइल वैन में रिवर्स-नीलामी स्कोरिंग।",
        btn_find_match: "कोल्ड चेन मैच खोजें",
        btn_accept_offer: "ऑफर स्वीकारें व क्षमता आरक्षित करें",
        btn_cancel_booking: "बुकिंग रद्द करें",
        data_source_simulated: "डेटा स्रोत: सिम्युलेटेड (डेमो)",
        data_status_fresh: "डेटा स्थिति: ताज़ा",
        solar_simulation_notice: "सोलर फॉलबैक: सरलीकृत सिमुलेशन (प्रभावी क्षमता = उपलब्ध क्षमता × सौर विश्वसनीयता)। हार्डवेयर बाद के चरण में है।",
        crop_mango: "आम (केसर / हापुस)",
        crop_tomato: "टमाटर",
        crop_grapes: "अंगूर",
        crop_onion: "प्याज",
        crop_strawberry: "स्ट्रॉबेरी",
        crop_pomegranate: "अनार",
        crop_cashew_apple: "काजू सेब",

        // Index / Auth (needs native-speaker review)
        auth_welcome: "कोल्डब्रिज एआई में आपका स्वागत है",
        auth_subtitle: "पे-पर-यूज़ कोल्ड चेन लॉजिस्टिक्स और स्मार्ट क्रॉस-एसेट मैचिंग",
        tab_sign_in: "साइन इन",
        tab_register: "पंजीकरण",
        label_email: "ईमेल पता",
        label_password: "पासवर्ड",
        btn_sign_in: "साइन इन",
        demo_logins_title: "त्वरित डेमो लॉगिन (महाराष्ट्र डेमो डेटासेट):",
        label_full_name: "पूरा नाम",
        label_phone: "फ़ोन नंबर",
        label_role: "मैं इस रूप में पंजीकरण करना चाहता हूँ:",
        btn_create_account: "खाता बनाएं",

        // Operator Portal (needs native-speaker review)
        operator_portal: "ऑपरेटर पोर्टल",
        nav_my_assets: "मेरी संपत्तियां",
        nav_active_bookings: "सक्रिय बुकिंग",
        nav_surplus_inv: "अतिरिक्त स्टॉक व इन्वेंटरी",
        nav_utilization: "क्षमता उपयोग",
        nav_sri_queue: "SRI प्राथमिकता कतार",
        nav_add_static: "शीतगृह जोड़ें",
        nav_add_van: "सोलर वैन जोड़ें",
        fleet_title: "शीतलन बुनियादी ढांचा बेड़ा",
        fleet_subtitle: "अपने पंजीकृत स्थिर शीतगृहों और मोबाइल सौर शीतलन वैन का प्रबंधन करें।",
        btn_refresh: "ताज़ा करें",

        // Buyer Portal (needs native-speaker review)
        buyer_portal: "खरीदार पोर्टल",
        nav_surplus_market: "अतिरिक्त उपज बाज़ार",
        nav_my_orders: "मेरे ऑर्डर",
        nav_demand_forecasts: "मांग पूर्वानुमान",
        surplus_market_title: "शीघ्र खराब होने वाली अतिरिक्त उपज बाज़ार",
        surplus_market_subtitle: "सुविधा ऑपरेटरों द्वारा प्रमाणित छूट पर ताज़ा प्री-कूल्ड उपज प्राप्त करें।",

        // Admin Portal (needs native-speaker review)
        admin_portal: "सिस्टम एडमिन",
        nav_system_overview: "सिस्टम अवलोकन",
        nav_simulation_controls: "सिमुलेशन नियंत्रण",
        nav_audit_trail: "ऑडिट ट्रेल",
        admin_title: "प्लेटफ़ॉर्म संचालन डैशबोर्ड",
        admin_subtitle: "सिस्टम स्वास्थ्य, बुनियादी ढांचे की संख्या और सक्रिय कोल्ड-चेन आवंटन।",

        // Part 5 E2: Farmer Asset Type Clarity & Filter Keys (Hindi translation needs native-speaker review)
        type_storage_room: "कोल्ड स्टोरेज रूम",
        type_solar_van: "सोलर कूलिंग वैन",
        storage_delivery_note: "आप अपनी उपज इस केंद्र तक पहुँचाते हैं।",
        van_pickup_note: "यह वैन आपकी उपज लेने आपके खेत पर आती है।",
        filter_all_types: "सभी विकल्प",
        filter_storage_only: "केवल स्टोरेज रूम",
        filter_vans_only: "केवल सोलर वैन",
        no_solar_van_in_range: "दायरे में कोई सोलर वैन उपलब्ध नहीं है",
        no_storage_room_in_range: "दायरे में कोई स्टोरेज रूम उपलब्ध नहीं है",
        label_service_radius: "सेवा दायरा",
        label_pickup_eta: "पिकअप समय",
        label_effective_capacity: "प्रभावी क्षमता",
        label_simulated: "सिम्युलेटेड",
        label_supported_crops: "समर्थित फसलें",
        label_temp_range: "तापमान सीमा",
        label_daily_rate: "प्रति दिन दर",

        // Part 4 D2: Public Directory Keys (Hindi translation needs native-speaker review)
        dir_card_title: "सार्वजनिक कोल्ड स्टोरेज निर्देशिका – नाशिक और पुणे",
        dir_judge_statement: "ये नाशिक और पुणे में वास्तविक कोल्ड स्टोरेज सुविधाएं हैं, जो सार्वजनिक निर्देशिकाओं से ली गई हैं। एक किसान सीधे उनसे संपर्क कर सकता है। हमारे प्रोटोटाइप में रैंकिंग और बोलियां अभी भी सिम्युलेटेड हैं।",
        dir_filter_district: "जिला फ़िल्टर",
        dir_filter_all: "सभी जिले",
        dir_filter_nashik: "नाशिक",
        dir_filter_pune: "पुणे",
        dir_search_placeholder: "सुविधा का नाम, क्षेत्र या पते से खोजें...",
        dir_btn_search: "खोजें",
        dir_badge_public: "सार्वजनिक सूची",
        dir_badge_not_partner: "कोल्डब्रिज पार्टनर नहीं है",
        dir_btn_call: "कॉल करें",
        dir_btn_copy_phone: "नंबर कॉपी करें",
        dir_btn_show_map: "नक्शे पर देखें",
        dir_unverified_warning: "असत्यापित – पुष्टि के लिए कॉल करें",
        dir_no_phone: "कोई फ़ोन नंबर सूचीबद्ध नहीं है",
        dir_loading: "निर्देशिका सूचियां लोड हो रही हैं...",
        dir_empty: "आपके खोज मानदंडों से मेल खाने वाली कोई सार्वजनिक कोल्ड स्टोरेज सुविधा नहीं मिली।",
        dir_error: "सार्वजनिक निर्देशिका लोड करने में असमर्थ। कृपया बाद में पुनः प्रयास करें।",
        dir_copied_alert: "फ़ोन नंबर क्लिपबोर्ड पर कॉपी हो गया!"
    },
    mr: {
        brand_title: "❄️ कोल्डब्रिज एआय",
        farmer_portal: "शेतकरी पोर्टल",
        nav_overview: "आढावा",
        nav_add_produce: "पीक जोडा",
        nav_cooling_map: "शीतकरण नकाशा",
        nav_batches: "माझे पीक लॉट्स व SRI",
        nav_matches: "शीतकरण पर्याय",
        nav_bookings: "माझी बुकिंग्ज",
        logout: "बाहेर पडा",
        overview_title: "शेतकरी डॅशबोर्ड",
        overview_subtitle: "तुमची नोंदणीकृत पिके, खराब होण्याचा धोका (SRI) आणि शीतकरण पर्यायांचा मागोवा घ्या.",
        stat_batches: "📦 एकूण पीक लॉट्स",
        stat_produce: "⚖️ एकूण शेतमाल",
        stat_high_risk: "🚨 जास्त धोका असलेले पीक",
        recent_batches_title: "नुकतेच कापलेले पीक आणि SRI मूल्यमापन",
        refresh: "रिफ्रेश करा",
        register_title: "नवीन पीक लॉट नोंदवा",
        register_subtitle: "शेतातील तापमान नोंदवा आणि त्वरित पारदर्शक स्पॉइलेज रिस्क इंडेक्स (SRI) मिळवा.",
        crop_label: "पिकाचा प्रकार *",
        quantity_label: "कापणी प्रमाण (किलो) *",
        harvest_time_label: "कापणीची तारीख व वेळ *",
        ambient_temp_label: "परिसरातील तापमान (°C) *",
        location_label: "शेताचे स्थान (ओपनस्ट्रीटमॅप नकाशा) *",
        notes_label: "पिकाबद्दल तपशील व गुणवत्ता नोंद",
        btn_register_sri: "पीक नोंदवा आणि SRI मोजा",
        sri_title: "स्पॉइलेज रिस्क इंडेक्स (SRI)",
        sri_honesty: "पारदर्शक नियम-आधारित नमुना अंदाज (वैज्ञानिकदृष्ट्या प्रमाणित अचूक वेळ नाही)",
        urgency_low: "कमी धोका",
        urgency_medium: "मध्यम धोका",
        urgency_high: "गंभीर धोका (तातडीने शीतगृह आवश्यक)",
        cooling_matches_title: "शीतगृह आणि सोलर व्हॅन जुळणी",
        cooling_matches_subtitle: "स्थिर शीतगृहे आणि फिरत्या सौर व्हॅन्सची पारदर्शक रिव्हर्स-लिलाव क्रमवारी.",
        btn_find_match: "शीतकरण पर्याय शोधा",
        btn_accept_offer: "ऑफर स्वीकारा व जागा आरक्षित करा",
        btn_cancel_booking: "बुकिंग रद्द करा",
        data_source_simulated: "डेटा स्रोत: सिम्युलेटेड (नमुना)",
        data_status_fresh: "डेटा स्थिती: ताजी",
        solar_simulation_notice: "सोलर फॉलबॅक: सरलीकृत सिम्युलेशन (प्रभावी क्षमता = उपलब्ध क्षमता × सौर विश्वसनीयता). हार्डवेअर सेन्सर्स पुढील टप्प्यात आहेत.",
        crop_mango: "आंबा (केसर / हापूस)",
        crop_tomato: "टोमॅटो",
        crop_grapes: "द्राक्षे",
        crop_onion: "कांदा",
        crop_strawberry: "स्ट्रॉबेरी",
        crop_pomegranate: "डाळिंब",
        crop_cashew_apple: "काजू सफरचंद",

        // Index / Auth (needs native-speaker review)
        auth_welcome: "कोल्डब्रिज एआय मध्ये आपले स्वागत आहे",
        auth_subtitle: "पे-पर-यूज शीतकरण वाहतूक आणि स्मार्ट मालमत्ता जुळणी",
        tab_sign_in: "साइन इन",
        tab_register: "नोंदणी",
        label_email: "ईमेल पत्ता",
        label_password: "पासवर्ड",
        btn_sign_in: "साइन इन",
        demo_logins_title: "त्वरित डेमो लॉगिन (महाराष्ट्र डेमो डेटासेट):",
        label_full_name: "पूर्ण नाव",
        label_phone: "फोन नंबर",
        label_role: "मला नोंदणी करायची आहे:",
        btn_create_account: "खाते तयार करा",

        // Operator Portal (needs native-speaker review)
        operator_portal: "ऑपरेटर पोर्टल",
        nav_my_assets: "माझी मालमत्ता",
        nav_active_bookings: "सक्रिय बुकिंग्ज",
        nav_surplus_inv: "अतिरिक्त शेतमाल व साठा",
        nav_utilization: "क्षमता वापर",
        nav_sri_queue: "SRI प्राधान्य रांग",
        nav_add_static: "शीतगृह जोडा",
        nav_add_van: "सोलर व्हॅन जोडा",
        fleet_title: "शीतकरण पायाभूत सुविधा ताफा",
        fleet_subtitle: "आपली नोंदणीकृत स्थिर शीतगृहे आणि फिरत्या सौर शीतकरण व्हॅन्सचे व्यवस्थापन करा.",
        btn_refresh: "रिफ्रेश करा",

        // Buyer Portal (needs native-speaker review)
        buyer_portal: "खरेदीदार पोर्टल",
        nav_surplus_market: "अतिरिक्त शेतमाल बाजारपेठ",
        nav_my_orders: "माझे ऑर्डर्स",
        nav_demand_forecasts: "मागणी अंदाज",
        surplus_market_title: "लवकर संपणारा अतिरिक्त शेतमाल बाजार",
        surplus_market_subtitle: "सुविधा चालकांनी प्रमाणित केलेल्या सवलतीच्या दरात ताजी थंड केलेली पिके मिळवा.",

        // Admin Portal (needs native-speaker review)
        admin_portal: "सिस्टम ॲडमिन",
        nav_system_overview: "प्रणाली आढावा",
        nav_simulation_controls: "सिम्युलेशन नियंत्रणे",
        nav_audit_trail: "ऑडिट नोंदी",
        admin_title: "प्लॅटफॉर्म ऑपरेशन्स डॅशबोर्ड",
        admin_subtitle: "सिस्टम आरोग्य, पायाभूत सुविधांची संख्या आणि सक्रिय शीतकरण वाटप.",

        // Part 5 E2: Farmer Asset Type Clarity & Filter Keys (Marathi translation needs native-speaker review)
        type_storage_room: "कोल्ड स्टोरेज रूम",
        type_solar_van: "सौर कुलिंग व्हॅन",
        storage_delivery_note: "तुम्ही तुमचा शेतमाल या केंद्रापर्यंत पोहोचवता.",
        van_pickup_note: "ही व्हॅन शेतमाल उचलण्यासाठी तुमच्या शेतावर येते.",
        filter_all_types: "सर्व पर्याय",
        filter_storage_only: "फक्त स्टोरेज रूम",
        filter_vans_only: "फक्त सोलर व्हॅन",
        no_solar_van_in_range: "मर्यादेत कोणतीही सौर व्हॅन उपलब्ध नाही",
        no_storage_room_in_range: "मर्यादेत कोणतीही स्टोरेज रूम उपलब्ध नाही",
        label_service_radius: "सेवा मर्यादा",
        label_pickup_eta: "पिकअप वेळ",
        label_effective_capacity: "प्रभावी क्षमता",
        label_simulated: "सिम्युलेटेड",
        label_supported_crops: "समर्थित पिके",
        label_temp_range: "तापमान श्रेणी",
        label_daily_rate: "प्रति दिवस दर",

        // Part 4 D2: Public Directory Keys (Marathi translation needs native-speaker review)
        dir_card_title: "सार्वजनिक कोल्ड स्टोरेज निर्देशिका – नाशिक आणि पुणे",
        dir_judge_statement: "या नाशिक आणि पुण्यातील सार्वजनिक निर्देशिकांमधून घेतलेल्या खऱ्या कोल्ड स्टोरेज सुविधा आहेत. शेतकरी थेट त्यांच्याशी संपर्क साधू शकतात. आमच्या प्रोटोटाइपमधील रँकिंग आणि बोली अद्याप सिम्युलेटेड आहेत.",
        dir_filter_district: "जिल्हा फिल्टर",
        dir_filter_all: "सर्व जिल्हे",
        dir_filter_nashik: "नाशिक",
        dir_filter_pune: "पुणे",
        dir_search_placeholder: "सुविधेचे नाव, परिसर किंवा पत्त्यानुसार शोधा...",
        dir_btn_search: "शोधा",
        dir_badge_public: "सार्वजनिक यादी",
        dir_badge_not_partner: "कोल्डब्रिज पार्टनर नाही",
        dir_btn_call: "कॉल करा",
        dir_btn_copy_phone: "नंबर कॉपी करा",
        dir_btn_show_map: "नकाशावर पहा",
        dir_unverified_warning: "पडताळणी बाकी – खात्रीसाठी कॉल करा",
        dir_no_phone: "कोणताही फोन नंबर नोंदवलेला नाही",
        dir_loading: "निर्देशिका यादी लोड होत आहे...",
        dir_empty: "तुमच्या निकषांशी जुळणारी कोणतीही सार्वजनिक कोल्ड स्टोरेज सुविधा आढळली नाही.",
        dir_error: "सार्वजनिक निर्देशिका लोड करता आली नाही. कृपया नंतर पुन्हा प्रयत्न करा.",
        dir_copied_alert: "फोन नंबर क्लिपबोर्डवर कॉपी झाला!"
    }
};

let currentLanguage = 'en';

export function getLanguage() {
    return currentLanguage;
}

export function setLanguage(lang) {
    if (translations[lang]) {
        currentLanguage = lang;
        try {
            localStorage.setItem('coldbridge_lang', lang);
        } catch (_) {}
        applyTranslations();
    }
}

export function t(key) {
    const dict = translations[currentLanguage] || translations.en;
    return dict[key] || translations.en[key] || key;
}

export function applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const translated = t(key);
        if (translated) {
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                el.placeholder = translated;
            } else {
                el.textContent = translated;
            }
        }
    });

    // Update document language attribute
    document.documentElement.lang = currentLanguage;
}

export function initI18n() {
    let saved = 'en';
    try {
        saved = localStorage.getItem('coldbridge_lang') || 'en';
    } catch (_) {}
    if (!translations[saved]) saved = 'en';
    currentLanguage = saved;
    applyTranslations();
}
