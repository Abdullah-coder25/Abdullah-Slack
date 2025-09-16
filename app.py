#!/usr/bin/env python3
"""
Abdullah Slack Clone - Real-time chat application
Built with Streamlit + Supabase for the Longhorn Startup assignment
"""

import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time
import json
from streamlit_supabase_auth import login_form, logout_button
from typing import List, Dict, Optional, Any

# Page config
st.set_page_config(
    page_title="Abdullah Slack",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Slack-like appearance
st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        max-width: none;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #3f0f40;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Chat message styling */
    .chat-message {
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 8px;
        background-color: #f8f9fa;
        border-left: 3px solid #007bff;
    }
    
    .chat-message-own {
        background-color: #007bff;
        color: white;
        border-left: 3px solid #0056b3;
        margin-left: 20px;
    }
    
    /* Channel list styling */
    .channel-item {
        padding: 4px 8px;
        margin: 2px 0;
        border-radius: 4px;
        cursor: pointer;
    }
    
    .channel-item:hover {
        background-color: rgba(255,255,255,0.1);
    }
    
    .channel-active {
        background-color: #007bff;
        color: white;
    }
    
    /* User status */
    .user-online {
        color: #28a745;
    }
    
    .user-offline {
        color: #6c757d;
    }
    
    /* Message input */
    .stTextArea textarea {
        border-radius: 20px;
        border: 1px solid #ddd;
        padding: 10px 15px;
    }
    
    /* Compact layout */
    .element-container {
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Load environment variables
if os.path.exists(".env"):
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    is_local = True
else:
    SUPABASE_URL = st.secrets.get("SUPABASE_URL")
    SUPABASE_ANON_KEY = st.secrets.get("SUPABASE_ANON_KEY")
    is_local = False

# Check for missing configuration
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    st.error("🚨 **Configuration Error: Missing Supabase Credentials**")
    
    if is_local:
        st.markdown("""
        **Local Development Setup Needed:**
        
        1. Create a `.env` file in your project root
        2. Add your Supabase credentials:
        ```
        SUPABASE_URL=https://your-project-ref.supabase.co
        SUPABASE_ANON_KEY=your_anon_key_here
        ```
        3. Get these values from [Supabase Dashboard](https://supabase.com/dashboard) → Settings → API
        
        📖 **Need help?** Check the README.md for detailed setup instructions.
        """)
    else:
        st.markdown("""
        **Streamlit Cloud Setup Needed:**
        
        1. Go to your [Streamlit Cloud dashboard](https://share.streamlit.io/)
        2. Find this app and click on it
        3. Click the **⚙️ Settings** button (usually in the top right)
        4. Go to **Secrets** tab
        5. Add your secrets in TOML format (**quotes are required**):
        ```toml
        SUPABASE_URL = "https://your-project-ref.supabase.co"
        SUPABASE_ANON_KEY = "your_anon_key_here"
        ```
        6. Click **Save** and the app will restart automatically
        """)
    
    st.stop()

# Initialize Supabase client
@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

supabase = init_supabase()

# Helper functions
def get_authenticated_supabase(session):
    """Get authenticated Supabase client"""
    auth_supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    access_token = session.get("access_token")
    if access_token:
        auth_supabase.auth.set_session(access_token, session.get("refresh_token", ""))
    return auth_supabase

def create_or_update_user_profile(auth_supabase, user):
    """Create or update user profile"""
    try:
        user_id = user.get("id")
        email = user.get("email", "")
        
        # Extract username from email or use GitHub username
        username = email.split("@")[0] if email else f"user_{user_id[:8]}"
        
        # Get GitHub user data if available
        user_metadata = user.get("user_metadata", {})
        avatar_url = user_metadata.get("avatar_url", "")
        display_name = user_metadata.get("full_name") or user_metadata.get("name") or username
        
        # Upsert user profile
        result = auth_supabase.table("user_profiles").upsert({
            "id": user_id,
            "username": username,
            "display_name": display_name,
            "avatar_url": avatar_url,
            "status": "online",
            "updated_at": datetime.utcnow().isoformat()
        }).execute()
        
        # Ensure default workspace and general channel exist
        ensure_default_workspace_and_channel(auth_supabase, user_id)
        
        return result.data[0] if result.data else None
    except Exception as e:
        st.error(f"Error creating user profile: {e}")
        return None

def ensure_default_workspace_and_channel(auth_supabase, user_id):
    """Ensure default workspace and general channel exist"""
    try:
        # Check if default workspace exists
        workspace_result = auth_supabase.table("workspaces").select("*").eq("name", "Default Workspace").execute()
        
        if not workspace_result.data:
            # Create default workspace
            workspace_result = auth_supabase.table("workspaces").insert({
                "name": "Default Workspace",
                "description": "Main workspace for the team",
                "created_by": user_id
            }).execute()
            
            if workspace_result.data:
                workspace_id = workspace_result.data[0]["id"]
            else:
                return
        else:
            workspace_id = workspace_result.data[0]["id"]
        
        # Check if general channel exists
        channel_result = auth_supabase.table("channels").select("*").eq("name", "general").eq("workspace_id", workspace_id).execute()
        
        if not channel_result.data:
            # Create general channel
            channel_result = auth_supabase.table("channels").insert({
                "workspace_id": workspace_id,
                "name": "general",
                "description": "General discussion channel",
                "created_by": user_id
            }).execute()
            
            if channel_result.data:
                channel_id = channel_result.data[0]["id"]
                # Auto-join the creator to the general channel
                join_channel(auth_supabase, user_id, channel_id)
        else:
            channel_id = channel_result.data[0]["id"]
            # Make sure user is a member of general channel
            join_channel(auth_supabase, user_id, channel_id)
            
    except Exception as e:
        # Silently handle errors to avoid breaking the user experience
        pass

def get_user_channels(auth_supabase, user_id):
    """Get channels user is a member of"""
    try:
        result = auth_supabase.table("channels")\
            .select("*, channel_members!inner(*)")\
            .eq("channel_members.user_id", user_id)\
            .execute()
        return result.data
    except Exception as e:
        st.error(f"Error fetching channels: {e}")
        return []

def get_channel_messages(auth_supabase, channel_id, limit=50):
    """Get messages for a specific channel"""
    try:
        # First get messages
        result = auth_supabase.table("messages")\
            .select("*")\
            .eq("channel_id", channel_id)\
            .order("created_at", desc=False)\
            .limit(limit)\
            .execute()
        
        messages = result.data
        
        # Then get user profiles for each message
        for message in messages:
            try:
                user_result = auth_supabase.table("user_profiles")\
                    .select("*")\
                    .eq("id", message["user_id"])\
                    .execute()
                
                if user_result.data:
                    message["user_profiles"] = user_result.data[0]
                else:
                    message["user_profiles"] = {"display_name": "Unknown User", "username": "unknown"}
            except:
                message["user_profiles"] = {"display_name": "Unknown User", "username": "unknown"}
        
        return messages
    except Exception as e:
        st.error(f"Error fetching messages: {e}")
        return []

def get_direct_messages(auth_supabase, user_id, other_user_id, limit=50):
    """Get direct messages between two users"""
    try:
        # Check if this is a demo user
        demo_user_ids = ["a1b2c3d4-e5f6-7890-abcd-ef1234567890", "b2c3d4e5-f6g7-8901-bcde-fg2345678901"]
        if other_user_id in demo_user_ids:
            # Get demo messages from session state
            conversation_key = f"{user_id}_{other_user_id}"
            
            # Initialize with some demo messages if none exist
            if "demo_messages" not in st.session_state:
                st.session_state.demo_messages = {}
            
            if conversation_key not in st.session_state.demo_messages:
                # Add some initial demo messages
                st.session_state.demo_messages[conversation_key] = [
                    {
                        "id": "demo-init-1",
                        "user_id": other_user_id,
                        "recipient_id": user_id,
                        "content": "Hey! Welcome to the Slack clone! 👋",
                        "created_at": "2024-01-15T10:00:00Z",
                        "message_type": "text"
                    },
                    {
                        "id": "demo-init-2", 
                        "user_id": other_user_id,
                        "recipient_id": user_id,
                        "content": "This is a demo conversation to show how messaging works. Try sending me a message!",
                        "created_at": "2024-01-15T10:01:00Z",
                        "message_type": "text"
                    }
                ]
            
            demo_messages = st.session_state.demo_messages[conversation_key]
            
            # Add user profiles to demo messages
            for msg in demo_messages:
                if msg["user_id"] == user_id:
                    msg["user_profiles"] = {"display_name": "You", "username": "you"}
                else:
                    # Find the demo user info
                    demo_user_names = {
                        "a1b2c3d4-e5f6-7890-abcd-ef1234567890": {"display_name": "Alex Johnson", "username": "alex"},
                        "b2c3d4e5-f6g7-8901-bcde-fg2345678901": {"display_name": "Sarah Chen", "username": "sarah"}
                    }
                    msg["user_profiles"] = demo_user_names.get(msg["user_id"], {"display_name": "Demo User", "username": "demo"})
            
            return demo_messages
        
        # First get messages
        result = auth_supabase.table("messages")\
            .select("*")\
            .is_("channel_id", "null")\
            .or_(f"and(user_id.eq.{user_id},recipient_id.eq.{other_user_id}),and(user_id.eq.{other_user_id},recipient_id.eq.{user_id})")\
            .order("created_at", desc=False)\
            .limit(limit)\
            .execute()
        
        messages = result.data
        
        # Then get user profiles for each message
        for message in messages:
            try:
                user_result = auth_supabase.table("user_profiles")\
                    .select("*")\
                    .eq("id", message["user_id"])\
                    .execute()
                
                if user_result.data:
                    message["user_profiles"] = user_result.data[0]
                else:
                    message["user_profiles"] = {"display_name": "Unknown User", "username": "unknown"}
            except:
                message["user_profiles"] = {"display_name": "Unknown User", "username": "unknown"}
        
        return messages
    except Exception as e:
        st.error(f"Error fetching direct messages: {e}")
        return []

def send_direct_message(auth_supabase, user_id, recipient_id, content):
    """Send a direct message to another user"""
    try:
        # Check if this is a demo user
        demo_user_ids = ["a1b2c3d4-e5f6-7890-abcd-ef1234567890", "b2c3d4e5-f6g7-8901-bcde-fg2345678901"]
        if recipient_id in demo_user_ids:
            # For demo users, we'll simulate the message being sent
            # In a real app, this would go to the database
            return {
                "id": f"demo-msg-{int(time.time())}",
                "user_id": user_id,
                "recipient_id": recipient_id,
                "content": content.strip(),
                "message_type": "text",
                "created_at": datetime.utcnow().isoformat()
            }
        
        # For real users, send to database
        result = auth_supabase.table("messages").insert({
            "user_id": user_id,
            "recipient_id": recipient_id,
            "content": content.strip(),
            "message_type": "text",
            "channel_id": None
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        st.error(f"Error sending direct message: {e}")
        return None

def get_all_users(auth_supabase, exclude_user_id=None):
    """Get all users for direct messaging"""
    try:
        query = auth_supabase.table("user_profiles").select("*")
        if exclude_user_id:
            query = query.neq("id", exclude_user_id)
        result = query.execute()
        users = result.data
        
        # Add demo users for demonstration
        demo_users = [
            {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "username": "alex",
                "display_name": "Alex Johnson",
                "avatar_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face",
                "status": "online"
            },
            {
                "id": "b2c3d4e5-f6g7-8901-bcde-fg2345678901", 
                "username": "sarah",
                "display_name": "Sarah Chen",
                "avatar_url": "https://images.unsplash.com/photo-1494790108755-2616b612b5bc?w=150&h=150&fit=crop&crop=face",
                "status": "online"
            }
        ]
        
        # Filter out current user from demo users
        if exclude_user_id:
            demo_users = [u for u in demo_users if u["id"] != exclude_user_id]
        
        return users + demo_users
    except Exception as e:
        st.error(f"Error fetching users: {e}")
        # Return demo users as fallback
        return [
            {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "username": "alex",
                "display_name": "Alex Johnson", 
                "avatar_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face",
                "status": "online"
            },
            {
                "id": "b2c3d4e5-f6g7-8901-bcde-fg2345678901",
                "username": "sarah", 
                "display_name": "Sarah Chen",
                "avatar_url": "https://images.unsplash.com/photo-1494790108755-2616b612b5bc?w=150&h=150&fit=crop&crop=face",
                "status": "online"
            }
        ]

def add_reaction(auth_supabase, message_id, user_id, emoji):
    """Add a reaction to a message"""
    try:
        result = auth_supabase.table("message_reactions").insert({
            "message_id": message_id,
            "user_id": user_id,
            "emoji": emoji
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        # Ignore all reaction errors silently for demo
        return None

def remove_reaction(auth_supabase, message_id, user_id, emoji):
    """Remove a reaction from a message"""
    try:
        result = auth_supabase.table("message_reactions")\
            .delete()\
            .eq("message_id", message_id)\
            .eq("user_id", user_id)\
            .eq("emoji", emoji)\
            .execute()
        return True
    except Exception as e:
        # Ignore all reaction errors silently for demo
        return False

def get_message_reactions(auth_supabase, message_id):
    """Get all reactions for a message"""
    try:
        # First get reactions
        result = auth_supabase.table("message_reactions")\
            .select("*")\
            .eq("message_id", message_id)\
            .execute()
        
        reactions = result.data
        
        # Then get user profiles for each reaction
        for reaction in reactions:
            try:
                user_result = auth_supabase.table("user_profiles")\
                    .select("*")\
                    .eq("id", reaction["user_id"])\
                    .execute()
                
                if user_result.data:
                    reaction["user_profiles"] = user_result.data[0]
                else:
                    reaction["user_profiles"] = {"display_name": "Unknown User", "username": "unknown"}
            except:
                reaction["user_profiles"] = {"display_name": "Unknown User", "username": "unknown"}
        
        return reactions
    except Exception as e:
        return []

def send_message(auth_supabase, user_id, channel_id, content):
    """Send a message to a channel"""
    try:
        result = auth_supabase.table("messages").insert({
            "user_id": user_id,
            "channel_id": channel_id,
            "content": content.strip(),
            "message_type": "text"
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        st.error(f"Error sending message: {e}")
        return None

def join_channel(auth_supabase, user_id, channel_id):
    """Join a user to a channel"""
    try:
        result = auth_supabase.table("channel_members").insert({
            "user_id": user_id,
            "channel_id": channel_id
        }).execute()
        return True
    except Exception as e:
        if "duplicate key" not in str(e).lower():
            st.error(f"Error joining channel: {e}")
        return False

def create_channel(auth_supabase, user_id, workspace_id, name, description=""):
    """Create a new channel"""
    try:
        # Create channel
        result = auth_supabase.table("channels").insert({
            "workspace_id": workspace_id,
            "name": name,
            "description": description,
            "created_by": user_id
        }).execute()
        
        if result.data:
            channel_id = result.data[0]["id"]
            # Auto-join creator to channel
            join_channel(auth_supabase, user_id, channel_id)
            return result.data[0]
        return None
    except Exception as e:
        st.error(f"Error creating channel: {e}")
        return None

def format_message_time(created_at):
    """Format message timestamp"""
    try:
        msg_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        now = datetime.now(msg_time.tzinfo)
        diff = now - msg_time
        
        if diff.days > 0:
            return msg_time.strftime("%m/%d/%Y %I:%M %p")
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            return "just now"
    except:
        return created_at

# Set environment variable for streamlit-supabase-auth
os.environ["SUPABASE_KEY"] = SUPABASE_ANON_KEY

# Authentication
session = login_form(
    url=SUPABASE_URL,
    apiKey=SUPABASE_ANON_KEY,
    providers=["github"]
)

# Initialize session state
if "current_channel" not in st.session_state:
    st.session_state.current_channel = None
if "current_dm_user" not in st.session_state:
    st.session_state.current_dm_user = None
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "channel"  # "channel" or "dm"
if "message_count" not in st.session_state:
    st.session_state.message_count = 0
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()
if "demo_messages" not in st.session_state:
    st.session_state.demo_messages = {}

if session:
    # User is authenticated
    user = session["user"]
    user_id = user.get("id")
    auth_supabase = get_authenticated_supabase(session)
    
    # Create/update user profile
    user_profile = create_or_update_user_profile(auth_supabase, user)
    
    # Sidebar - Channel Navigation
    with st.sidebar:
        st.markdown("### 💬 Abdullah Slack")
        
        # User info
        if user_profile:
            col1, col2 = st.columns([1, 3])
            with col1:
                if user_profile.get("avatar_url"):
                    st.markdown(f'<img src="{user_profile["avatar_url"]}" width="40" style="border-radius: 50%;">', unsafe_allow_html=True)
                else:
                    st.markdown("👤")
            with col2:
                st.markdown(f"**{user_profile.get('display_name', 'User')}**")
                st.markdown('<span class="user-online">● Online</span>', unsafe_allow_html=True)
        
        logout_button(apiKey=SUPABASE_ANON_KEY)
        
        st.divider()
        
        # Channels section
        st.markdown("### 📋 Channels")
        
        # Get user's channels
        channels = get_user_channels(auth_supabase, user_id)
        
        # Auto-join general channel if not already joined
        if not any(ch["name"] == "general" for ch in channels):
            join_channel(auth_supabase, user_id, 1)  # Assuming general channel ID is 1
            channels = get_user_channels(auth_supabase, user_id)
        
        # Set default channel
        if not st.session_state.current_channel and channels:
            st.session_state.current_channel = channels[0]
        
        # Channel list
        for channel in channels:
            channel_name = f"# {channel['name']}"
            is_active = (st.session_state.view_mode == "channel" and 
                        st.session_state.current_channel and 
                        st.session_state.current_channel['id'] == channel['id'])
            
            if st.button(channel_name, key=f"channel_{channel['id']}", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state.current_channel = channel
                st.session_state.current_dm_user = None
                st.session_state.view_mode = "channel"
                st.rerun()
        
        st.divider()
        
        # Direct Messages section
        st.markdown("### 💬 Direct Messages")
        
        # Get all users for DMs
        all_users = get_all_users(auth_supabase, user_id)
        
        for dm_user in all_users:
            user_name = f"@ {dm_user.get('display_name') or dm_user.get('username', 'User')}"
            is_active = (st.session_state.view_mode == "dm" and 
                        st.session_state.current_dm_user and 
                        st.session_state.current_dm_user['id'] == dm_user['id'])
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if dm_user.get('avatar_url'):
                    st.markdown(f'<img src="{dm_user["avatar_url"]}" width="24" style="border-radius: 50%;">', unsafe_allow_html=True)
                else:
                    st.markdown("👤")
            with col2:
                if st.button(user_name, key=f"dm_{dm_user['id']}", use_container_width=True, type="primary" if is_active else "secondary"):
                    st.session_state.current_dm_user = dm_user
                    st.session_state.current_channel = None
                    st.session_state.view_mode = "dm"
                    st.rerun()
        
        if not all_users:
            st.info("No other users online")
        
        st.divider()
        
        # Create new channel
        with st.expander("➕ Create Channel"):
            with st.form("create_channel"):
                new_channel_name = st.text_input("Channel name", placeholder="e.g., random")
                new_channel_desc = st.text_input("Description (optional)", placeholder="Channel description")
                
                if st.form_submit_button("Create Channel"):
                    if new_channel_name.strip():
                        # Clean channel name
                        clean_name = new_channel_name.strip().lower().replace(" ", "-")
                        new_channel = create_channel(auth_supabase, user_id, 1, clean_name, new_channel_desc)
                        if new_channel:
                            st.success(f"Created #{clean_name}")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.error("Please enter a channel name")
        
        # Join existing channels
        with st.expander("🔍 Browse Channels"):
            try:
                # Get all public channels
                all_channels_result = auth_supabase.table("channels")\
                    .select("*")\
                    .eq("is_private", False)\
                    .execute()
                
                user_channel_ids = [ch["id"] for ch in channels]
                available_channels = [ch for ch in all_channels_result.data if ch["id"] not in user_channel_ids]
                
                for channel in available_channels:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"#{channel['name']}")
                        if channel.get('description'):
                            st.caption(channel['description'])
                    with col2:
                        if st.button("Join", key=f"join_{channel['id']}", use_container_width=True):
                            if join_channel(auth_supabase, user_id, channel['id']):
                                st.success("Joined!")
                                time.sleep(1)
                                st.rerun()
                            
            except Exception as e:
                st.error(f"Error loading channels: {e}")
    
    # Main chat area
    if st.session_state.view_mode == "channel" and st.session_state.current_channel:
        current_channel = st.session_state.current_channel
        
        # Channel header
        st.markdown(f"## #{current_channel['name']}")
        if current_channel.get('description'):
            st.caption(current_channel['description'])
    
    elif st.session_state.view_mode == "dm" and st.session_state.current_dm_user:
        current_dm_user = st.session_state.current_dm_user
        
        # DM header
        col1, col2 = st.columns([1, 10])
        with col1:
            if current_dm_user.get('avatar_url'):
                st.markdown(f'<img src="{current_dm_user["avatar_url"]}" width="40" style="border-radius: 50%;">', unsafe_allow_html=True)
            else:
                st.markdown("👤")
        with col2:
            st.markdown(f"## {current_dm_user.get('display_name') or current_dm_user.get('username', 'User')}")
            st.caption("Direct Message")
        
    # Auto-refresh messages
    if st.session_state.view_mode in ["channel", "dm"]:
        if time.time() - st.session_state.last_refresh > 5:  # Refresh every 5 seconds
            st.session_state.last_refresh = time.time()
            st.rerun()
        
        # Messages container
        messages_container = st.container()
        
        with messages_container:
            # Get and display messages
            if st.session_state.view_mode == "channel" and st.session_state.current_channel:
                messages = get_channel_messages(auth_supabase, st.session_state.current_channel['id'])
                context_name = f"#{st.session_state.current_channel['name']}"
            elif st.session_state.view_mode == "dm" and st.session_state.current_dm_user:
                messages = get_direct_messages(auth_supabase, user_id, st.session_state.current_dm_user['id'])
                context_name = f"@{st.session_state.current_dm_user.get('display_name') or st.session_state.current_dm_user.get('username', 'User')}"
                
            else:
                messages = []
                context_name = ""
            
            if messages:
                for msg in messages:
                    # Message container
                    msg_container = st.container()
                    
                    with msg_container:
                        col1, col2 = st.columns([1, 20])
                        
                        with col1:
                            # Avatar
                            if msg.get('user_profiles') and msg['user_profiles'].get('avatar_url'):
                                st.markdown(f'<img src="{msg["user_profiles"]["avatar_url"]}" width="32" style="border-radius: 50%;">', unsafe_allow_html=True)
                            else:
                                st.markdown("👤")
                        
                        with col2:
                            # Message header
                            user_name = "Unknown User"
                            if msg.get('user_profiles'):
                                user_name = msg['user_profiles'].get('display_name') or msg['user_profiles'].get('username') or "User"
                            
                            time_str = format_message_time(msg['created_at'])
                            
                            st.markdown(f"**{user_name}** <small style='color: #666;'>{time_str}</small>", unsafe_allow_html=True)
                            
                            # Message content
                            st.markdown(msg['content'])
                            
                            # Reactions and actions
                            col_reactions, col_actions = st.columns([4, 1])
                            
                            with col_reactions:
                                # Get and display reactions
                                reactions = get_message_reactions(auth_supabase, msg['id'])
                                
                                if reactions:
                                    # Group reactions by emoji
                                    reaction_counts = {}
                                    user_reactions = {}
                                    
                                    for reaction in reactions:
                                        emoji = reaction['emoji']
                                        if emoji not in reaction_counts:
                                            reaction_counts[emoji] = 0
                                            user_reactions[emoji] = []
                                        reaction_counts[emoji] += 1
                                        user_reactions[emoji].append(reaction['user_profiles']['display_name'] or reaction['user_profiles']['username'])
                                    
                                    # Display reaction buttons
                                    reaction_cols = st.columns(len(reaction_counts))
                                    for i, (emoji, count) in enumerate(reaction_counts.items()):
                                        with reaction_cols[i]:
                                            # Check if current user has reacted with this emoji
                                            user_has_reacted = any(r['user_id'] == user_id and r['emoji'] == emoji for r in reactions)
                                            button_type = "primary" if user_has_reacted else "secondary"
                                            
                                            if st.button(f"{emoji} {count}", key=f"reaction_{msg['id']}_{emoji}", type=button_type):
                                                if user_has_reacted:
                                                    remove_reaction(auth_supabase, msg['id'], user_id, emoji)
                                                else:
                                                    add_reaction(auth_supabase, msg['id'], user_id, emoji)
                                                st.rerun()
                            
                            with col_actions:
                                # Quick reaction buttons
                                reaction_col1, reaction_col2, reaction_col3 = st.columns(3)
                                with reaction_col1:
                                    if st.button("👍", key=f"quick_thumbs_up_{msg['id']}", help="Add thumbs up"):
                                        add_reaction(auth_supabase, msg['id'], user_id, "👍")
                                        st.rerun()
                                with reaction_col2:
                                    if st.button("❤️", key=f"quick_heart_{msg['id']}", help="Add heart"):
                                        add_reaction(auth_supabase, msg['id'], user_id, "❤️")
                                        st.rerun()
                                with reaction_col3:
                                    if st.button("😄", key=f"quick_laugh_{msg['id']}", help="Add laugh"):
                                        add_reaction(auth_supabase, msg['id'], user_id, "😄")
                                        st.rerun()
                    
                    st.divider()
            else:
                st.info(f"No messages in {context_name} yet. Start the conversation!")
        
        # Message input (fixed at bottom)
        st.divider()
        
        col1, col2 = st.columns([5, 1])
        
        with col1:
            message_input = st.text_area(
                "Message",
                placeholder=f"Message {context_name}",
                height=80,
                label_visibility="collapsed",
                key=f"msg_input_{st.session_state.message_count}"
            )
        
        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)  # Spacing for alignment
            send_button = st.button("Send", type="primary", use_container_width=True, key=f"send_btn_{st.session_state.message_count}")
        
        if send_button and message_input and message_input.strip():
            # Send message
            if st.session_state.view_mode == "channel" and st.session_state.current_channel:
                sent_message = send_message(auth_supabase, user_id, st.session_state.current_channel['id'], message_input)
            elif st.session_state.view_mode == "dm" and st.session_state.current_dm_user:
                sent_message = send_direct_message(auth_supabase, user_id, st.session_state.current_dm_user['id'], message_input)
                
                # If it's a demo user, store the message in session state
                demo_user_ids = ["a1b2c3d4-e5f6-7890-abcd-ef1234567890", "b2c3d4e5-f6g7-8901-bcde-fg2345678901"]
                if st.session_state.current_dm_user['id'] in demo_user_ids and sent_message:
                    conversation_key = f"{user_id}_{st.session_state.current_dm_user['id']}"
                    if conversation_key not in st.session_state.demo_messages:
                        st.session_state.demo_messages[conversation_key] = []
                    st.session_state.demo_messages[conversation_key].append(sent_message)
            else:
                sent_message = None
            
            if sent_message:
                st.session_state.message_count += 1
                st.rerun()
    
    else:
        st.markdown("## Welcome to Abdullah Slack! 👋")
        st.markdown("Select a channel or start a direct message from the sidebar to begin chatting.")
        
        channels = get_user_channels(auth_supabase, user_id)
        if not channels:
            st.info("You're not a member of any channels yet. Join the #general channel from the sidebar!")

else:
    # User not authenticated
    st.markdown("# 💬 Abdullah Slack")
    st.markdown("### Real-time team collaboration made simple")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        **Features:**
        - 📋 **Channels & Workspaces** - Organize conversations by topic
        - 💬 **Real-time Messaging** - Chat with your team instantly  
        - 👥 **User Profiles** - GitHub integration with avatars
        - 🔒 **Secure** - Row-level security with Supabase
        - 📱 **Responsive** - Works on desktop and mobile
        
        **Sign in with GitHub to get started!**
        """)
    
    st.divider()
    st.markdown("*Built for the Longhorn Startup assignment by Abdullah*")

# Auto-refresh indicator
if session and st.session_state.current_channel:
    with st.empty():
        st.markdown(f'<div style="position: fixed; top: 10px; right: 10px; background: rgba(0,0,0,0.7); color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">Auto-refresh: {5 - int(time.time() - st.session_state.last_refresh)}s</div>', unsafe_allow_html=True)