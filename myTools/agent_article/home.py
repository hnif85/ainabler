import streamlit as st
from phi.agent import Agent
from phi.model.groq import Groq
from phi.tools.googlesearch import GoogleSearch

def create_research_agent():
    return Agent(
        name="Research Agent",
        description="This agent is responsible for researching the latest trends that user want to research.",
        model=Groq(
            id="llama-3.3-70b-versatile",
            api_key="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"
        ),
        instructions="You need to research all latest trends and provide the user with the best information using tools provided.",
        tools=[GoogleSearch(
            fixed_max_results=5,        
        )],
        show_tool_calls=True,
    )

def extract_content(response):
    """Extract only the content from the research response"""
    if hasattr(response, 'content') and response.content:
        return response.content
    elif isinstance(response, str):
        return response
    return "No content found in response"

def main():
    st.title("Research Assistant")
    
    # Input field for research topic
    research_topic = st.text_input("Enter your research topic:", "")
    
    # Add checkbox to toggle between full response and content only
    show_full_response = st.checkbox("Show full response (including tool calls)", value=False)
    
    if st.button("Research"):
        if research_topic:
            with st.spinner("Researching..."):
                # Create agent
                research_agent = create_research_agent()
                
                # Get research results
                response = research_agent.run(research_topic)
                
                # Display results
                st.markdown("### Research Results")
                
                if show_full_response:
                    st.markdown(response)
                    
                    # Display tool calls
                    st.markdown("### Research Sources")
                    tool_calls = research_agent.get_tool_calls()
                    if tool_calls:
                        for i, call in enumerate(tool_calls):
                            st.markdown(f"**Source {i+1}:**")
                            st.code(str(call))
                else:
                    # Display only the content
                    content = extract_content(response)
                    st.markdown(content)
        else:
            st.warning("Please enter a research topic")

    # Add some usage instructions
    with st.sidebar:
        st.markdown("""
        1. Enter your research topic in the text field
        2. Click the 'Research' button
        3. Wait for the results to appear
        4. Review both the research summary and sources used
        """)

if __name__ == "__main__":
    main()