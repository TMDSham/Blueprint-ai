import streamlit as st
from io import BytesIO
from PIL import Image
import base64
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title='Blueprint take-off AI', page_icon='👁️')

st.markdown('# CAD Blueprint take-off AI')
api_key = st.text_input('OpenRouter API Key', '', type='password')

# Get user inputs
img_input = st.file_uploader('Images', accept_multiple_files=True)

# Send API request
if st.button('Send'):
    if not api_key:
        st.warning('API Key required')
        st.stop()
    
    msg = {'role': 'user', 'content': []}
    msg['content'].append({'type': 'text', 'text': 'Provide a take-off of the quantities from this engineering drawing returning ONLY as a markdown table.'})
    
    for img in img_input:
        if img.name.split('.')[-1].lower() not in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
            st.warning('Only .jpg, .png, .gif, or .webp are supported')
            st.stop()
        encoded_img = base64.b64encode(img.read()).decode('utf-8')
        msg['content'].append(
            {
                'type': 'image_url',
                'image_url': {
                    'url': f'data:image/jpeg;base64,{encoded_img}',
                    'detail': 'low'
                }
            }
        )

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': 'openai/gpt-4o',
        'messages': [msg],
        'max_tokens': 500
    }
    response = requests.post(
        'https://openrouter.ai/api/v1/chat/completions',
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        response_data = response.json()
        response_msg = response_data['choices'][0]['message']['content']
        
        # 🟡 Check if response contains HTML and parse it with BeautifulSoup
        if "<table" in response_msg:
            soup = BeautifulSoup(response_msg, "html.parser")
            # Extract text from each table cell
            rows = []
            for row in soup.find_all("tr"):
                cells = [cell.get_text(strip=True) for cell in row.find_all(["td", "th"])]
                rows.append(cells)
            # Display as a markdown table
            if rows:
                markdown_table = "| " + " | ".join(rows[0]) + " |\n"
                markdown_table += "| " + " | ".join(["---"] * len(rows[0])) + " |\n"
                for row in rows[1:]:
                    markdown_table += "| " + " | ".join(row) + " |\n"
                response_msg = markdown_table
            else:
                response_msg = "No table data found."
    
    else:
        response_msg = f"Error: {response.status_code}\n{response.text}"

    # Display user input and response
    with st.chat_message('user'):
        for i in msg['content']:
            if i['type'] == 'text':
                st.write(i['text'])
            else:
                with st.expander('Attached Image'):
                    img = Image.open(BytesIO(base64.b64decode(i['image_url']['url'][23:])))
                    st.image(img)
    
    if response_msg:
        with st.chat_message('assistant'):
            st.markdown(response_msg)
