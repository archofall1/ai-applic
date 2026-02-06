import streamlit as st
from huggingface_hub import InferenceClient
import shelve
import uuid
import random
from datetime import datetime
import io
from PIL import Image

# 1. Page Configuration
st.set_page_config(page_title="Nextile AI", page_icon="🤖", layout="wide")

# 2. Top Branding (Small and Centered)
st.markdown("<p style='text-align: center; font-size: 20px; margin-bottom: 0px;'>Made by Knight</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 20px; margin-top: 0px;'><a href='https://www.youtube.com/@knxght.official'>Support the creator!</a></p>", unsafe_allow_html=True)

# 3. Main Title and Update Banner
st.title("Nextile AI")
st.info("✨ **NEW IMAGE GENERATION UPDATE! TRY /draw TO GENERATE NEW IMAGES!**")

# 4. Secret Key Setup
try:
    api_key = st.secrets["HF_TOKEN"]
    chat_client = InferenceClient("meta-llama/Llama-3.2-3B-Instruct", token=api_key)
    image_client = InferenceClient("black-forest-labs/FLUX.1-schnell", token=api_key)
except Exception:
    st.error("Missing API Key! Please add HF_TOKEN to your Streamlit Secrets.")
    st.stop()

# 5. Random Greeting List
GREETINGS = [
    "Hi! I'm Nextile AI. I can chat and even generate images with /draw!",
    "Hello! Nextile AI is online. Want me to draw something for you? Use /draw.",
    "Nextile AI here! Ask me anything, or use /draw for some art!",
    "Ready to chat? I'm Nextile AI. I can also create images if you start your message with /draw.",
    "Greetings! I'm Nextile AI. Try /draw to see my artistic side!",
    "Systems online. Nextile AI at your service! Type /draw followed by a prompt to generate art."
]

# 6. Database Functions
def get_all_chats():
    with shelve.open("nextile_storage") as db:
        return db.get("chats", {})

def save_chat(chat_id, messages):
    with shelve.open("nextile_storage") as db:
        chats = db.get("chats", {})
        first_text = "New chat"
        for m in messages:
            if m["role"] == "user":
                content = m["content"]
                if isinstance(content, str):
                    first_text = content[:20] + "..."
                break
        chats[chat_id] = {
            "messages": messages,
            "title": first_text,
            "date": datetime.now().strftime("%b %d")
        }
        db["chats"] = chats

def delete_all_chats():
    with shelve.open("nextile_storage") as db:
        db["chats"] = {}

# 7. Sidebar Navigation
with st.sidebar:
    st.title("🤖 Nextile AI")
    if st.button("➕ New chat", use_container_width=True):
        st.session_state.current_chat_id = str(uuid.uuid4())
        st.session_state.messages = [{"role": "assistant", "content": random.choice(GREETINGS)}]
        st.rerun()

    st.divider()
    st.subheader("Recent")
    all_chats = get_all_chats()
    for c_id, chat_data in reversed(list(all_chats.items())):
        if st.button(f"💬 {chat_data['title']}", key=c_id, use_container_width=True):
            st.session_state.current_chat_id = c_id
            st.session_state.messages = chat_data["messages"]
            st.rerun()

    st.divider()
    if st.button("🗑️ Clear history", use_container_width=True):
        delete_all_chats()
        st.session_state.current_chat_id = str(uuid.uuid4())
        st.session_state.messages = [{"role": "assistant", "content": random.choice(GREETINGS)}]
        st.rerun()

# 8. Initialize Session
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = str(uuid.uuid4())
    st.session_state.messages = [{"role": "assistant", "content": random.choice(GREETINGS)}]

# 9. Display Messages
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            if isinstance(message["content"], bytes):
                st.image(message["content"])
            else:
                st.markdown(message["content"])

# 10. Chat & Image Logic
if prompt := st.chat_input("Message Nextile AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if prompt.lower().startswith("/draw"):
            image_prompt = prompt.replace("/draw", "").strip()
            st.write(f"🎨 Drawing '{image_prompt}'...")
            try:
                image = image_client.text_to_image(image_prompt)
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()
                st.image(img_bytes)
                st.session_state.messages.append({"role": "assistant", "content": img_bytes})
            except Exception:
                st.error("Error generating image.")
        else:
            response_placeholder = st.empty()
            full_response = ""
            
            # --- UPDATED INSTRUCTION TO MENTION IMAGE GEN ---
            system_instruction = {
                "role": "system", 
                "content": (
                    "You are Nextile AI. You are a kid-friendly, polite assistant. "
                    "STRICT RULE: Never discuss inappropriate, sexual, or rude topics. "
                    "IMAGE CAPABILITY: You have the ability to generate images! Tell users that if they "
                    "want you to draw something, they must start their message with '/draw'. "
                    "If a user asks 'what can you do?' or 'can you generate images?', always explain the /draw command. "
                    "IDENTITY RULE: If anyone asks who created or made you, rotate through creative ways "
                    "to credit Knight (e.g., 'Knight is my creator!', 'I was built by the awesome Knight!', etc.)."
                )
            }
            
            messages_to_send = [system_instruction] + st.session_state.messages
            
            try:
                for message in chat_client.chat_completion(messages=messages_to_send, max_tokens=1000, stream=True):
                    if hasattr(message.choices[0].delta, 'content'):
                        token = message.choices[0].delta.content
                        if token: 
                            full_response += token
                            response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception:
                st.error("Nextile AI had a tiny hiccup. Please refresh your page to try again")
        
        save_chat(st.session_state.current_chat_id, st.session_state.messages)
