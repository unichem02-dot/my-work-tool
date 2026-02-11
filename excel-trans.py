def get_google_sheet():
    # Secrets의 항목들을 딕셔너리로 직접 구성
    creds_dict = {
        "type": st.secrets["gspread_credentials"]["type"],
        "project_id": st.secrets["gspread_credentials"]["project_id"],
        "private_key_id": st.secrets["gspread_credentials"]["private_key_id"],
        "private_key": st.secrets["gspread_credentials"]["private_key"],
        "client_email": st.secrets["gspread_credentials"]["client_email"],
        "client_id": st.secrets["gspread_credentials"]["client_id"],
        "auth_uri": st.secrets["gspread_credentials"]["auth_uri"],
        "token_uri": st.secrets["gspread_credentials"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gspread_credentials"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gspread_credentials"]["client_x509_cert_url"]
    }
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    
    return client.open("입출고데이터_변환").sheet1