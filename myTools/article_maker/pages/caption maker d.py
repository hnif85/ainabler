import streamlit as st
import yaml
from groq import Groq
from tavily import TavilyClient
import json
from datetime import datetime

groq_api_key = st.session_state.groq_key
tavily_api_key = st.session_state.tavily_key

# Load example captions from YAML
def load_example_captions():
    example_captions = """
    instagram:
        lifestyle: |
            🌟 Living my best life one adventure at a time! ✨
            Can't believe how beautiful today was - sometimes the simplest moments bring the biggest joy 💫
            
            Who else is feeling those weekend vibes? Drop a 🙌 below!
            
            #LifestyleBlogger #WeekendVibes #LivingMyBestLife #Happiness
        
        business: |
            💼 Transform your business strategy with these game-changing tips!
            
            Swipe through to discover how we achieved 150% growth in just 6 months 📈
            
            Save this post for later - you won't want to miss these insights! 
            
            #BusinessTips #Entrepreneurship #GrowthStrategy
            
    twitter:
        tech: |
            New research shows AI models achieving 95% accuracy in medical diagnoses. This could revolutionize healthcare accessibility worldwide. 
            
            Thread 🧵 on the implications:
            #AI #Healthcare #Innovation
            
        news: |
            Breaking: Major policy changes announced for renewable energy sector. Expected to create 50,000 new jobs by 2025.
            
            Full analysis below:
            #RenewableEnergy #Policy #Sustainability
            
    tiktok:
        entertainment: |
            POV: When you finally find that perfect song for your video 🎵✨
            Wait for it... 😂
            #FYP #viral #trending #music
        
        tutorial: |
            The hack you didn't know you needed! 🤯
            Follow for more life-changing tips ⬆️
            #LearnOnTikTok #Tutorial #Hack #viral
    """
    return yaml.safe_load(example_captions)

# Page config
st.set_page_config(page_title="Social Media Caption Generator", layout="wide")
st.session_state

# Sidebar for API keys and configuration
with st.sidebar:
    st.header("Configuration")
    #groq_api_key = st.text_input("Enter Groq API Key", type="password")
    #tavily_api_key = st.text_input("Enter Tavily API Key", type="password")
    
    # Model selection
    model_option = st.selectbox(
        "Select Language Model",
        ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama3-70b-8192"]
    )
    
    # Platform selection
    platform = st.selectbox(
        "Select Social Media Platform",
        ["Instagram", "X (Twitter)", "TikTok"]
    )
    
    # Audience selection
    target_audience = st.selectbox(
        "Select Target Audience",
        ["Teenagers (13-19)", "Young Adults (20-35)", "Adults (36-50)", "Children (with parent supervision)"]
    )

# Main content
st.title("Social Media Caption Generator")

# Input fields
content_topic = st.text_area("Enter your content topic or main message")
keywords = st.text_input("Enter relevant keywords (comma-separated)")

# Reference caption section
example_captions = load_example_captions()
use_custom_reference = st.checkbox("Use custom reference caption")

if use_custom_reference:
    reference_caption = st.text_area("Enter your reference caption")
else:
    # Show example captions based on selected platform
    platform_key = platform.lower().replace(" ", "").replace("(", "").replace(")", "")
    if platform_key in example_captions:
        caption_type = st.selectbox(
            "Select reference caption type",
            list(example_captions[platform_key].keys())
        )
        reference_caption = example_captions[platform_key][caption_type]
    else:
        reference_caption = ""

def create_prompt(platform, topic, keywords, audience, reference,riset):
    """Generate platform-specific prompts"""
    base_prompt = f"""
    Topic: {topic}
    Keywords: {keywords}
    Target Audience: {audience}
    Reference Style: {reference}
    Research: {riset}
    Bahasa : Indonesia

    Create a {platform} caption that matches and input input research as part of the caption the reference style while maintaining originality.
    """
    
    platform_specifics = {
        "Instagram": """
        Requirements:
        - Upbeat and positive tone
        - Strategic emoji placement
        - Engaging questions or call-to-action
        - 3-5 relevant hashtags
        - Maximum 2200 characters
        - Similar style to reference but not copied
        """,
        
        "X (Twitter)": """
        Requirements:
        - Professional and concise
        - Data-driven when relevant
        - 2-3 strategic hashtags
        - Conversation starter
        - Maximum 280 characters
        - Similar style to reference but not copied
        """,
        
        "TikTok": """
        Requirements:
        - Trendy and attention-grabbing
        - Popular TikTok terminology
        - Call-to-action for engagement
        - 4-6 trending hashtags
        - Maximum 2200 characters
        - Similar style to reference but not copied
        """
    }
    
    return base_prompt + platform_specifics.get(platform, "Invalid platform selected")

# Generate caption button

tavily_client = TavilyClient(api_key=tavily_api_key)
if st.button("Generate Caption"):
    if not content_topic:
        st.error("Please enter a content topic.")         
    else:
        with st.spinner("Generating caption..."):

            riset_result = tavily_client.get_search_context(query=content_topic)
            #riset_result = riset.content
            with st.expander("Research Findings"):
                st.write(riset_result)
            # Create prompt with reference
            prompt = create_prompt(
                platform, 
                content_topic, 
                keywords, 
                target_audience,
                reference_caption,
                riset_result   
            )

            with st.expander("Prompt"):
                st.write(prompt)
            
            # Generate caption
            client = Groq(api_key=groq_api_key)
            completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional social media {platform} content writer."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=model_option,
                temperature=0.7,
            )
            
            caption = completion.choices[0].message.content
            
            # Display results
            st.subheader("Generated Caption:")
            st.write(caption)
            
            
# Footer
st.markdown("---")
st.markdown("Created with ❤️ using Streamlit, Groq, and Tavily")