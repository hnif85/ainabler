# README: LLM Use Case Project

## Overview
This project explores use cases for Large Language Models (LLMs) with agentic capabilities, primarily utilizing **Streamlit** as the front-end framework and integrating with **Groq API** for LLM functionalities. The application is designed for easy deployment and interaction, offering robust features powered by state-of-the-art AI models.

## Prerequisites
Before running the project, ensure the following:

1. **Python Installed:** This project requires Python 3.8 or newer. If not installed, download it from [python.org](https://www.python.org/downloads/).
2. **Groq API Key:** Obtain an API key from Groq and keep it handy.
3. **Internet Connection:** The application requires a stable internet connection to communicate with the Groq API.

## Installation

Follow these steps to set up the project locally:

1. **Clone the Repository**
   ```bash
   https://github.com/hnif85/ainabler.git
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**
   Create a `.env` file in the root directory and add your Groq API key:
   ```env
   GROQ_API_KEY=your_api_key_here
   ```

## Usage

1. **Run the Application**
   Start the Streamlit app using the following command:
   ```bash
   streamlit run app.py
   ```

2. **Access the Application**
   Open your web browser and navigate to `http://localhost:8501` to access the application interface.

3. **Interact with the Features**
   - Input prompts or queries for the LLM.
   - Leverage agentic capabilities for complex tasks.
   - View real-time results powered by Groq API.

## Features
- **Agentic LLMs:** Supports advanced agentic tasks.
- **Streamlit Interface:** User-friendly and interactive front end.
- **Groq Integration:** High-performance LLM operations via Groq API.

## Troubleshooting
- **Missing Dependencies:** Ensure all dependencies are installed correctly by re-running `pip install -r requirements.txt`.
- **Invalid API Key:** Verify your Groq API key in the `.env` file.
- **Connection Issues:** Check your internet connection and API access.

## Acknowledgments
Special thanks to the Groq team for providing robust API support and the Streamlit community for their excellent resources.

---

Enjoy using the project! For any issues, feel free to raise a GitHub issue or contact the maintainer.
