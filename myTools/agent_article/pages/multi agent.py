import streamlit as st
from phi.agent import Agent
from phi.tools.googlesearch import GoogleSearch
from phi.model.groq import Groq
import sqlite3
from datetime import datetime
import json
from datetime import datetime
from phi.tools.website import WebsiteTools
from phi.model.google import Gemini


def convert_to_ddmmyyyy(date_string):
    """
    Mengubah format tanggal dengan mikrodetik menjadi dd/mm/yyyy.

    :param date_string: Tanggal dalam format string (misal: '2025-01-01 20:40:20.933344').
    :return: Tanggal dalam format dd/mm/yyyy.
    """
    try:
        # Format input dengan mikrodetik
        current_format = "%Y-%m-%d %H:%M:%S.%f"
        # Parse tanggal
        date_object = datetime.strptime(date_string, current_format)
        # Ubah ke format dd/mm/yyyy
        formatted_date = date_object.strftime('%d-%m-%Y')
        return formatted_date
    except ValueError as e:
        return f"Error: {e}"

def create_db():
    conn = sqlite3.connect('articles.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS articles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  topic TEXT,
                  style TEXT,
                  word_count INTEGER,
                  focus_areas TEXT,
                  additional_instructions TEXT,
                  article_content TEXT,
                  sources TEXT,
                  model TEXT,
                  created_at TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_article(topic, style, word_count, focus_areas, additional_instructions, article_content,sources, model):
    conn = sqlite3.connect('articles.db')
    c = conn.cursor()
    c.execute('''INSERT INTO articles 
                 (topic, style, word_count, focus_areas, additional_instructions, 
                  article_content, sources, created_at, model)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (topic, style, word_count, focus_areas, additional_instructions,
               article_content, json.dumps(sources), datetime.now(), model))
    conn.commit()
    conn.close()

def get_saved_articles():
    conn = sqlite3.connect('articles.db')
    c = conn.cursor()
    c.execute('SELECT * FROM articles ORDER BY created_at DESC')
    articles = c.fetchall()
    conn.close()
    return articles

def create_agents(model):
    web_agent = Agent(
        name="Web Research Agent",
        role="Research current information and news",
        #model=Groq(
            #id=model,
            #api_key="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"),
        model=Gemini(
            id=model,
            api_key=("AIzaSyB-DJi1VqfUYvK2ml5bJ5C9UDrtoFL4a58")
        ),
        tools=[GoogleSearch(
            fixed_max_results=5,        
        ),WebsiteTools()],
        instructions=[
            "Research thoroughly and include sources",
            "Focus on finding recent and relevant information",
            "Extract key points and trends",
            "if user give website link then extract information from that website use website tool"
        ],
        show_tool_calls=True,
        markdown=True,
    )
    
    content_agent = Agent(
        name="Content Writing Agent",
        role="Write engaging articles based on research",
        #model=Groq(
            #id=model,
            #api_key="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"),
        model=Gemini(
            id=model,
            api_key=("AIzaSyB-DJi1VqfUYvK2ml5bJ5C9UDrtoFL4a58")
        ),
        instructions=[
            "Write in a clear, engaging style",
            "Structure content with proper headings",
            "Include introduction and conclusion",
            "Maintain professional tone"
        ],
        show_tool_calls=True,
        markdown=True,
    )
    
    return Agent(
        team=[web_agent, content_agent],
        model=Groq(
            id="llama3-groq-8b-8192-tool-use-preview",
            api_key="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"),
        instructions=[
            "Conduct thorough research first",
            "Create well-structured articles",
            "Include sources and citations",
            "Ensure factual accuracy"
        ],
        show_tool_calls=True,
        markdown=True,
        debug_mode=True
    )

def main():
    # Initialize database
    create_db()

    st.set_page_config("Article Generator", page_icon="📝",layout="wide")
    
    # Create tabs
    tab1, tab2 = st.tabs(["Generate Article", "View Saved Articles"])
    
    with tab1:
        st.title("Research Article Generator")
        
        # Sidebar for configurations
        st.sidebar.header("Article Settings")
        article_style = st.sidebar.selectbox(
            "Writing Style",
            ["Informative", "Technical", "Casual", "Academic"]
        )

        model = st.sidebar.selectbox(
            "LLM Model",
            ["gemini-2.0-flash-exp","llama3-70b-8192","llama3-8b-8192", "llama-3.3-70b-versatile", "mixtral-8x7b-32768"]
        )
        
        word_count = st.sidebar.slider(
            "Target Word Count",
            min_value=300,
            max_value=2000,
            value=800,
            step=100
        )
        
        # Main content area
        st.markdown("### Topic Information")

        topic = st.text_area("Main Topic:", placeholder="Enter your main topic")
        
        col1, col2 = st.columns(2)
        with col1:
            focus_areas = st.text_area(
                "Focus Areas (comma-separated):",
                placeholder="trends, statistics, future outlook"
            )
        
        with col2:
            additional_instructions = st.text_area(
            "Additional Instructions:",
            placeholder="Any specific aspects you want to focus on or exclude..."
        )         
        

        web_link = st.text_input("Website Link:", placeholder="Enter website link")
        
        if st.button("Generate Article"):
            if not topic:
                st.warning("Please enter a main topic")
                return
                
            with st.spinner("Researching and generating article..."):
                try:
                    # Create agent team
                    agent_team = create_agents(model)
                    
                    prompt = f"""
                                Write an article in Bahasa Indonesia about {topic}

                                Research Requirements:
                                - Must verify topic accuracy and correctness
                                - Required: Recent factual data and credible sources
                                - If insufficient research available, do not proceed with writing
                                - Include research findings within article content
                                - If website provided: {web_link}, analyze and incorporate relevant data

                                Article Specifications:
                                Length: {word_count} words
                                Style: {article_style}
                                Key Focus: {focus_areas}
                                Special Instructions: {additional_instructions}

                                Content Guidelines:
                                - Original structure tailored to topic
                                - Clear sections with descriptive headings
                                - Engaging narrative flow with topic sentences
                                - Evidence-based supporting details
                                - Proper citations for statistics and sources
                                - Natural paragraph transitions

                                Quality Checks:
                                1. Topic validation and correction if needed
                                2. Research integration verification
                                3. Structure appropriateness assessment
                                4. Source credibility confirmation
                                """
                    
                    # Get response
                    response = agent_team.run(prompt)
                    
                    # Process messages
                    messages = response.messages
                    article_content = None
                    research_content = None
                    sources = []
                    
                    for message in messages:
                        if (message.tool_name == 'transfer_task_to_content_writing_agent' and 
                            message.content is not None):
                            article_content = message.content
                        elif (message.tool_name == 'transfer_task_to_web_research_agent' and 
                              message.content is not None):
                            research_content = message.content
                            # Extract sources
                            lines = research_content.split('\n')
                            capture_sources = False
                            for line in lines:
                                if line.strip() == 'Sumber:':
                                    capture_sources = True
                                    continue
                                if capture_sources and line.strip().startswith('*'):
                                    sources.append(line.strip('* '))
                    
                    if article_content:
                        st.markdown("### Generated Article")
                        words_counted = len(article_content.split())
                        st.markdown(f"**Word Count:** {words_counted}")
                        st.markdown(article_content)
                        
                        # Display sources
                        if sources:
                            st.markdown("### Sources")
                            for i, source in enumerate(sources, 1):
                                with st.expander(f"Source {i}: {source}"):
                                    st.markdown(f"**Source:** {source}")
                                    if research_content:
                                        # Find relevant content from research
                                        for line in research_content.split('\n'):
                                            if line.strip().startswith('*'):
                                                st.markdown(f"- {line.strip('* ')}")
                        
                        # Save to database
                        save_article(topic, article_style, word_count, focus_areas,
                                   additional_instructions, article_content,sources, model)
                        st.success("Article generated and saved successfully!")
                    
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
    
    with tab2:
        st.title("Saved Articles")
        articles = get_saved_articles()

                
        for article in articles:
            date = str(article[8])
            formatted_date = convert_to_ddmmyyyy(date)

            with st.expander(f"Article: {article[1]} created at: {formatted_date}"):
                st.markdown("### Parameters")
                st.markdown(f"**Topic:** {article[1]}")
                st.markdown(f"**Style:** {article[2]}")
                st.markdown(f"**Word Count:** {article[3]}")
                st.markdown(f"**Focus Areas:** {article[4]}")
                st.markdown(f"**Additional Instructions:** {article[5]}")
                st.markdown(f"**Model:** {article[9]}")
                
                st.markdown("### Article Content")
                st.markdown(article[6])
                
                st.markdown("### Sources")
                sources = json.loads(article[7])
                for i, source in enumerate(sources, 1):
                    st.markdown(f"{i}. {source}")
                
                st.markdown(f"*Generated on: {article[8]}*")

if __name__ == "__main__":
    main()