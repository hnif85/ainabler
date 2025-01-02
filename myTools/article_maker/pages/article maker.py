import streamlit as st
import yaml
from tavily import TavilyClient
from groq import Groq
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import json
import os
import sqlite3
from datetime import datetime
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_name="articles.db"):
        """Initialize database connection and create table if it doesn't exist."""
        self.db_name = db_name
        self.create_table()
    
    def create_table(self):
        """Create articles table if it doesn't exist."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                version TEXT,
                metadata TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def save_article(self, title: str, content: str, version: str = "draft", metadata: dict = None):
        """Save article to database."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO articles (title, content, created_at, version, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, content, datetime.now(), version, str(metadata)))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            st.error(f"Error saving article to database: {str(e)}")
            raise
        finally:
            conn.close()
    
    def get_all_articles(self):
        """Retrieve all articles from database."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM articles ORDER BY created_at DESC')
        articles = cursor.fetchall()
        conn.close()
        return articles
    
    def get_article_by_id(self, article_id: int):
        """Retrieve specific article by ID."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM articles WHERE id = ?', (article_id,))
        article = cursor.fetchone()
        conn.close()
        return article
    
    def delete_article(self, article_id: int):
        """Delete an article by ID."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM articles WHERE id = ?', (article_id,))
        conn.commit()
        conn.close()

#tambahkan fungsi untuk create db untuk menyimpan data, minimal data yang dimasukkan adalah judul, isi artikel, dan tanggal pembuatan
#simpan dalam data sqlite3
#tambahkan fungsi untuk menampilkan data yang sudah disimpan, mungkin bisa ditab atau terserah anda enaknya gmaan

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

    @staticmethod
    def get_platform_specific_prompt(platform: str) -> str:
        """
        Returns platform-specific prompt template based on the selected platform.
        """
        platform_prompts = {
            "linkedin": """
                Buatkan artikel profesional untuk diposting di LinkedIn dengan kategori {kategori}
                dan gaya bahasa {tone}. Dengan jumlah kata sekitar {length}.
                
                Struktur artikel sebagai panduan (bukan hasil akhir):
                {structure}
                
                Bahan utama: {article_material}
                Hasil riset: {riset}
                Bahasa: {language}
                
                Panduan khusus LinkedIn:
                - Gunakan format yang mudah dibaca di mobile device
                - Berikan white space yang cukup antar paragraf
                - Mulai dengan hook yang kuat untuk menarik perhatian pembaca profesional
                - Fokus pada insight dan pembelajaran praktis
                - Sisipkan 2-3 hashtag relevan di akhir artikel
                - Akhiri dengan call-to-action untuk mendorong engagement
                - Target pembaca: Profesional dan decision maker
                - Tone: Professional namun tetap personal
                """,
                
            "medium": """
                Buatkan artikel mendalam untuk diposting di Medium dengan kategori {kategori}
                dan gaya bahasa {tone}. Dengan jumlah kata sekitar {length}.
                
                Struktur artikel sebagai panduan (bukan hasil akhir):
                {structure}
                
                Bahan utama: {article_material}
                Hasil riset: {riset}
                Bahasa: {language}
                
                Panduan khusus Medium:
                - Utamakan kedalaman analisis dan pembahasan
                - Gunakan subheading yang informatif dan menarik
                - Sertakan quotes atau data penting dalam format blockquote
                - Berikan contoh kasus atau studi kasus yang relevan
                - Tambahkan referensi dan sumber di akhir artikel
                - Gunakan storytelling yang mengalir
                - Target pembaca: Pembaca yang mencari pengetahuan mendalam
                - Tone: Edukatif dan exploratif
                """,
                
            "personal blog": """
                Buatkan artikel untuk personal blog dengan kategori {kategori}
                dan gaya bahasa {tone}. Dengan jumlah kata sekitar {length}.
                
                Struktur artikel sebagai panduan (bukan hasil akhir):
                {structure}
                
                Bahan utama: {article_material}
                Hasil riset: {riset}
                Bahasa: {language}
                
                Panduan khusus Blog:
                - Gunakan gaya penulisan yang lebih personal dan conversational
                - Tambahkan pengalaman atau opini pribadi yang relevan
                - Sertakan contoh praktis dan tips yang actionable
                - Gunakan bahasa yang lebih santai namun tetap informatif
                - Optimalkan untuk SEO dengan kata kunci yang relevan
                - Akhiri dengan pertanyaan untuk mendorong diskusi
                - Target pembaca: Pembaca umum yang tertarik dengan topik
                - Tone: Casual dan engaging
                """
        }
        
        return platform_prompts.get(platform.lower(), "Platform tidak tersedia")
    
    def create_article_prompt(self, riset: str, article_material: str, platform: str, kategori: str, length: str, tone: str) -> str:
        """Generate article prompt based on template, materials, and selected platform."""
        try:
            metadata = self.config["article_template"]["metadata"]
            structure = self._format_article_structure(self.config["article_template"]["structure"])
            
            platform_template = self.get_platform_specific_prompt(platform)
            
            return platform_template.format(
                kategori=kategori,
                tone=tone,
                length=length,
                structure=structure,
                article_material=article_material,
                riset=riset,
                language=metadata.get('language', 'Indonesia')
            )
            
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

    st.session_state

    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Create tabs
    tab1, tab2 = st.tabs(["Write Article", "View Saved Articles"])
    
    with tab1:
        st.title("Professional Article Writer")

        # Sidebar configuration
        with st.sidebar:
            st.header("Configuration")

            groq_api = st.session_state.groq_key
            tavily_api = st.session_state.tavily_key
            model = st.selectbox(
                "Select Model",
                ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama3-70b-8192"],
                help="Choose the AI model for article generation"
            )
            platform = st.selectbox(
                "Select Platform",
                ["LinkedIn", "Medium", "Personal Blog"],
                help="Choose the platform for the article"
            )
            kategori = st.selectbox(
                "Select Kategori",
                ["kesehatan", "teknologi", "pendidikan","lifestyle","bisnis","otomotif","hiburan","olahraga","kuliner","travel"],
                help="Choose the kategori for the article"
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
        st.write(article_material)

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
                    
                    # Research phase
                    with st.expander("Research Results"):
                        st.subheader("Generated Topic")
                        
                        
                        riset = tavily_client.get_search_context(query=topic)                    
                        st.subheader("Research Findings")
                        st.write(riset)

                    # Article generation phase
                    col1, col2 = st.columns([3,1])
                    with col1:
                                     
                        with st.expander(f"{topic} Ready Version"):
                            article_prompt = generator.create_article_prompt(riset, article_material, platform,kategori,target_length,tone)
                            #linkedin_prompt = f"Rewrite the following article for LinkedIn, maintaining professionalism while engaging the audience:\n\n{draft}"
                            linkedin_version = generator.generate_content(article_prompt, model, "Article writer")
                            st.markdown(linkedin_version)
                            metadata = {
                                    "tone": tone,
                                    "target_length": target_length,
                                    "model": model,
                                    "platform": "LinkedIn"
                                }
                            db_manager.save_article(topic, linkedin_version, "linkedin", metadata)
                            st.success("LinkedIn version saved to database!")

                    with col2:
                        st.write("apakah anda ingin menyimpan artikel ini?")                                                                   
                                

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            logger.error(f"Application error: {str(e)}")
    
    with tab2:
        st.title("Saved Articles")
        articles = db_manager.get_all_articles()
        
        if not articles:
            st.info("No articles saved yet. Generate some articles in the 'Write Article' tab!")
        else:
            for article in articles:
                with st.expander(f"{article[1]} - {article[3]} ({article[4]})"):
                    st.markdown(article[2])
                    if st.button(f"Delete Article {article[0]}", key=f"delete_{article[0]}"):
                        db_manager.delete_article(article[0])
                        st.success("Article deleted!")
                        st.rerun()

if __name__ == "__main__":
    main()