import streamlit as st
import yaml
from tavily import TavilyClient
from groq import Groq
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import json
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigManager:
    @staticmethod
    def load_yaml_template(file_path: str = "config.yaml") -> Dict[str, Any]:
        """Load and validate YAML configuration file."""
        try:
            with open(file_path, "r", encoding='utf-8') as file:
                config = yaml.safe_load(file)
            if not ConfigManager._validate_config(config):
                raise ValueError("Invalid configuration structure")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            st.error(f"Failed to load configuration: {str(e)}")
            return {}

    @staticmethod
    def _validate_config(config: Dict) -> bool:
        """Validate the configuration structure."""
        required_keys = ['article_template']
        return all(key in config for key in required_keys)

class ArticleGenerator:
    def __init__(self, groq_api: str):
        self.groq_client = Groq(api_key=groq_api) if groq_api else None
        self.config = ConfigManager.load_yaml_template()

    def create_article_prompt(self, riset: str, article_material: str) -> str:
        """Generate article prompt based on template and materials."""
        try:
            metadata = self.config["article_template"]["metadata"]
            structure = self.config["article_template"]["structure"]
            
            return f"""
            Buatkan artikel untuk diposting di {metadata['type']} dengan kategori {metadata['category']} 
            dan gaya bahasa {metadata['tone']}. Panjang artikel {metadata['length']}. 
            
            Struktur artikel sebagai panduan (bukan hasil akhir):
            {self._format_article_structure(structure)}
            
            Bahan utama: {article_material}
            Hasil riset: {riset}
            Bahasa: {metadata.get('language', 'Indonesia')}
            
            Panduan tambahan:
            - Gunakan lebih banyak narasi dibanding bullet point
            - Pastikan artikel mengalir dengan natural
            - Tambahkan data pendukung dari hasil riset
            - Sesuaikan dengan target audience {metadata['type']}
            """
        except Exception as e:
            logger.error(f"Error creating article prompt: {str(e)}")
            raise

    def _format_article_structure(self, structure: Dict) -> str:
        """Format article structure in a readable way."""
        formatted_sections = []
        
        # Format title
        formatted_sections.append(f"Judul: {structure['title']['description']}")
        
        # Format introduction
        formatted_sections.append(f"Pendahuluan: {structure['introduction']['content']}")
        
        # Format body sections
        formatted_sections.append("Isi:")
        for section in structure['body']['sections']:
            formatted_sections.append(f"- {section['title']}:")
            if 'content' in section:
              formatted_sections.append(f"   {section['content']}")
            if 'subsections' in section:
              for subsection in section['subsections']:
                formatted_sections.append(f"  - {subsection['title']}: {subsection['content']}")
        
        # Format conclusion
        formatted_sections.append(f"Kesimpulan: {structure['conclusion']['content']}")
        
        return "\n".join(formatted_sections)
    def generate_content(self, message: str, model: str, role: str = "helper") -> str:
        """Generate content using Groq API with error handling and retry logic."""
        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": f"You are great assistant for {role} and ready to help user with any occasion."},
                    {"role": "user", "content": message}
                ],
                model=model,
                temperature=0.5,
                max_tokens=4000,
                top_p=1,
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            raise

    def save_article(self, content: str, filename: Optional[str] = None) -> str:
        """Save generated article to file."""
        if not filename:
            filename = f"article_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        try:
            os.makedirs("articles", exist_ok=True)
            filepath = os.path.join("articles", filename)
            with open(filepath, "w", encoding='utf-8') as f:
                f.write(content)
            return filepath
        except Exception as e:
            logger.error(f"Error saving article: {str(e)}")
            raise

def main():
    st.set_page_config("Article Writer", layout="wide")
    st.title("Professional Article Writer")

    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        tavily_api = st.text_input("Tavily API Key", type="password")
        groq_api = st.text_input("Groq API Key", type="password")
        model = st.selectbox(
            "Select Model",
            ["llama-3.1-70b-versatile", "gpt-3.5-turbo"],
            help="Choose the AI model for article generation"
        )
        
        st.markdown("---")
        st.markdown("### Advanced Settings")
        with st.expander("Article Parameters"):
            tone = st.select_slider(
                "Writing Tone",
                options=["Formal", "Semi-formal", "Casual"],
                value="Semi-formal"
            )
            target_length = st.slider(
                "Target Length (words)",
                min_value=500,
                max_value=2000,
                value=1000,
                step=100
            )

    # Main content area
    article_material = st.text_area(
        "Article Material",
        height=200,
        help="Paste your raw material or notes here"
    )

    if not (tavily_api and groq_api):
        st.warning("Please enter your API keys in the sidebar to continue.")
        return

    try:
        generator = ArticleGenerator(groq_api)
        tavily_client = TavilyClient(api_key=tavily_api)
        
        if st.button("Generate Article", type="primary"):
            with st.spinner("Processing..."):
                # Generate topic summary
                query = f"Summarize the following into a 4-5 word topic: {article_material}"
                topic = generator.generate_content(query, model)

                st.write(topic)
                
                # Research phase
                with st.expander("Research Results"):
                    st.subheader("Generated Topic")
                    st.write(topic)
                    
                    riset = tavily_client.get_search_context(query=topic)                    
                    st.subheader("Research Findings")
                    st.write(riset)

                # Article generation phase
                col1, col2 = st.columns(2)
                with col1:
                    with st.expander("Draft Article"):
                        article_prompt = generator.create_article_prompt(riset, article_material)
                        draft = generator.generate_content(article_prompt, model, "Article Writer")
                        st.markdown(draft)
                        
                        if st.button("Save Draft"):
                            filepath = generator.save_article(draft)
                            st.success(f"Draft saved to {filepath}")

                with col2:
                    with st.expander("LinkedIn-Ready Version"):
                        linkedin_prompt = f"Rewrite the following article for LinkedIn, maintaining professionalism while engaging the audience:\n\n{draft}"
                        linkedin_version = generator.generate_content(linkedin_prompt, model, "LinkedIn Expert")
                        st.markdown(linkedin_version)
                        
                        if st.button("Save LinkedIn Version"):
                            filepath = generator.save_article(linkedin_version, "linkedin_version.md")
                            st.success(f"LinkedIn version saved to {filepath}")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        logger.error(f"Application error: {str(e)}")

if __name__ == "__main__":
    main()