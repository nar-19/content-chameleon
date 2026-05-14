import streamlit as st
import google.generativeai as genai
import os

# --- 1. Configure Gemini API Key ---
# Ensure your Streamlit secrets file (.streamlit/secrets.toml) has GEMINI_API_KEY defined.
# Example secrets.toml:
# GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("Gemini API Key not found in Streamlit secrets. Please add it as 'GEMINI_API_KEY'.")
    st.stop()
except Exception as e:
    st.error(f"Error configuring Gemini API: {e}")
    st.stop()

# --- 2. Agent Configuration ---
AGENT_NAME = "The Content Chameleon"
MODEL_NAME = "gemini-2.5-flash" # gemini-2.5-flash would be preferred if generally available and stable.
TEMPERATURE = 0.7 # A balance between creativity and consistency

# --- 3. Platform-specific knowledge base (Simulated by app logic) ---
# This dictionary contains instructions and desired output formats for each platform.
PLATFORM_GUIDELINES = {
    "LinkedIn": {
        "description": "Professional network for B2B, career development, and thought leadership. Focus on insights, value, and networking.",
        "output_format": """
**LinkedIn Post:**
- **Professional Summary (3-5 sentences):** [Summarize the core content with a professional angle, focusing on benefits/insights]
- **3 Key Takeaways (bullet points):**
    * Takeaway 1
    * Takeaway 2
    * Takeaway 3
- **Engaging Question:** [A question to spark professional discussion]
- **Relevant Hashtags (3-5):** #[hashtag1] #[hashtag2] #[hashtag3]
        """
    },
    "Instagram Story": {
        "description": "Visual-first, short, engaging, and ephemeral content. Focus on quick takes, behind-the-scenes, polls, and calls to action. Use concise text.",
        "output_format": """
**Instagram Story (Text Overlay/Visual Concept):**
- **Punchy Headline (1-2 sentences):** [Short, attention-grabbing text for story intro]
- **Key Message (1 short sentence):** [Core message/stat for mid-story]
- **Visual Prompt/Idea (e.g., fast-paced montage, poll sticker, animated text):** [Describe a visual concept, e.g., "Dynamic infographic animation", "Before/After product reveal", "Poll: 'Do you agree?' Yes/No"]
- **Relevant Hashtags (2-3, optional for story but good for discoverability):** #[hashtag1] #[hashtag2]
        """
    },
    "TikTok": {
        "description": "Short-form video platform driven by trends, sounds, and authenticity. Focus on quick hooks, entertainment, and relatable content. Visuals are key.",
        "output_format": """
**TikTok Video Concept:**
- **Video Hook (visual/text - 1-2 lines):** [Initial attention-grabbing moment, e.g., "POV: You're trying to...", "Watch this if you want to..."]
- **Core Message (concise - 1-2 sentences):** [The main point of the video, often delivered visually or via quick text]
- **Visual/Action Idea:** [Describe the visual actions/scenes, e.g., "Showcase product in a humorous way", "Quick tutorial of feature X", "Relatable reaction to a common problem"]
- **Trending Sound/Music Suggestion:** [e.g., "Upbeat viral sound", "Popular motivational audio"]
- **On-Screen Text Ideas (optional):** [Short phrases or stats to appear on screen for impact]
- **Relevant Hashtags (3-5):** #[hashtag1] #[hashtag2] #[hashtag3]
        """
    },
    "X/Twitter": {
        "description": "Microblogging platform for real-time updates, news, and quick interactions. Focus on conciseness, engagement, and trending topics. Max ~280 characters per tweet.",
        "output_format": """
**X/Twitter Post(s):**
- **Tweet 1 (Main Tweet - max ~280 chars):** [Concise, hook-driven message with a key point and an emoji] #[hashtag1]
- **Tweet 2 (Follow-up/Thread continuation - optional, max ~280 chars):** [Expand on an idea, add a stat, or provide a link (placeholder)]
- **Tweet 3 (Question/Call to action - optional, max ~280 chars):** [Engaging question or clear call to action]
- **Relevant Hashtags (2-3):** #[hashtag1] #[hashtag2]
        """
    },
    "Pinterest": {
        "description": "Visual discovery engine for inspiration and planning. Focus on high-quality evergreen visuals, DIYs, tutorials, and aspirational content.",
        "output_format": """
**Pinterest Pin Concept:**
- **Pin Title Idea (up to 100 chars):** [Catchy, descriptive title for the pin]
- **Pin Description Idea (up to 500 chars):** [Detailed description focusing on benefits, how-to, or inspiration, using keywords naturally]
- **Visual Concept/Image Brief:** [Describe the ideal image or short video for the pin, e.g., "High-quality infographic summarizing X steps", "Aesthetic product shot in a lifestyle setting", "Vertical video tutorial"]
- **Relevant Keywords/Hashtags (5-10):** #[keyword1] #[keyword2] #[keyword3] ...
        """
    }
}

# --- 4. Streamlit UI Layout ---
st.set_page_config(layout="wide", page_title=f"{AGENT_NAME} 🤖")

st.title(f"🤖 {AGENT_NAME}: Multi-Platform Content Adapter")
st.markdown("""
Welcome to **The Content Chameleon**! This AI agent helps you effortlessly adapt your master content
for various social media platforms. Just provide your core content, select your target platforms,
define your brand tone, and let the agent do the heavy lifting!
""")

st.subheader("1. Provide Your Master Content")
master_content = st.text_area(
    "Paste your core content here (e.g., blog post, video script excerpt, ad copy block):",
    height=200,
    placeholder="Example: 'Our new product, EcoGlow, is a sustainable skincare line that uses all-natural ingredients to rejuvenate your skin, reducing environmental impact while boosting your natural radiance. Available now!'"
)

st.subheader("2. Configure Adaptation Settings")
col1, col2 = st.columns(2)

with col1:
    target_platforms = st.multiselect(
        "Select Target Platforms:",
        list(PLATFORM_GUIDELINES.keys()),
        default=["LinkedIn", "X/Twitter"] # Pre-select common ones for quick start
    )

with col2:
    brand_tone = st.selectbox(
        "Select Desired Brand Tone:",
        ["Professional", "Informative", "Humorous", "Inspirational", "Casual", "Luxurious"],
        index=0 # Default to Professional
    )

key_messages = st.text_input(
    "Key Message(s) to Emphasize (optional, comma-separated):",
    placeholder="e.g., 'sustainable skincare, natural radiance, eco-friendly benefits'"
)

generate_button = st.button("✨ Generate Adapted Content")

# --- 5. Content Generation Logic (using Gemini as the agent's brain) ---
if generate_button:
    if not master_content:
        st.warning("Please provide some master content to adapt.")
    elif not target_platforms:
        st.warning("Please select at least one target platform.")
    else:
        st.subheader("3. Adapted Content Output")
        st.info("The Content Chameleon is at work, generating your content... This might take a moment.")

        # Initialize the Gemini model
        model = genai.GenerativeModel(MODEL_NAME)

        for platform in target_platforms:
            st.markdown(f"---")
            st.markdown(f"### 🌐 {platform} Content")

            platform_info = PLATFORM_GUIDELINES[platform]
            
            # Construct the detailed prompt for Gemini. This is where our "agentic" logic lives.
            # We instruct the LLM to act as the agent, using its knowledge and our structured prompt.
            prompt = f"""
            You are {AGENT_NAME}, an expert content adaptation agent. Your task is to take a piece of master content and adapt it specifically for the **{platform}** platform, adhering to its best practices, style, and typical audience engagement.

            **Master Content to Adapt:**
            ```
            {master_content}
            ```

            **Target Platform Context:**
            - **Platform Name:** {platform}
            - **Platform Description:** {platform_info['description']}
            - **Desired Brand Tone:** {brand_tone}
            - **Key Message(s) to Emphasize:** {key_messages if key_messages else "No specific messages provided; identify core themes from the master content."}

            **Instructions:**
            1.  Carefully read the master content and identify its core themes and value propositions.
            2.  Based on the platform description, adapt the content to be natively suitable for **{platform}**.
            3.  Ensure the generated content aligns with the **'{brand_tone}'** tone.
            4.  If specific key messages are provided, ensure they are prominently featured.
            5.  **Strictly adhere to the following output format for {platform}:**

            {platform_info['output_format']}

            Fill in all bracketed `[]` sections with actual generated content, do not leave them as placeholders.
            """
            
            try:
                with st.spinner(f"Adapting for {platform}..."):
                    response = model.generate_content(prompt, 
                                                      generation_config = { "temperature" : TEMPERATURE }
                                                     )
                    # Use response.text to get the generated markdown/text
                    st.markdown(response.text)
            except Exception as e:
                st.error(f"An error occurred while generating content for {platform}: {e}")
                st.markdown(f"*(Could not generate content for {platform}. Please check your inputs or API key.)*")

st.markdown("---")
st.markdown("💡 This application simulates an Agentic AI. The LLM (Gemini) acts as the 'agent' by interpreting detailed instructions, platform knowledge, and user input to generate context-aware content.")
st.markdown("*(Developed for a 30-minute hackathon concept)*")
