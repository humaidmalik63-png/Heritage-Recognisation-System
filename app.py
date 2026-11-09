import os
import uvicorn
import gradio as gr

try:
    import spaces
    @spaces.GPU(duration=60)
    def gpu_verify(text):
        """ZeroGPU accelerated health function."""
        return "ZeroGPU active"
except Exception:
    def gpu_verify(text):
        return "CPU active"

# Gradio status dashboard interface mounted on FastAPI
with gr.Blocks(title="Indian Heritage Monument Register API") as demo:
    gr.Markdown("""
    # 🏛️ Directorate of Archaeology & VLM Research
    ### Indian Heritage & Monument Register API
    - **Compute Environment:** Hugging Face Spaces (ZeroGPU Accelerated)
    - **Recognition Anchors:** 577 vectors (50 Indian + 50 International sites)
    - **Active Model:** openai/clip-vit-base-patch32 + gemini-3.1-flash-lite
    - **API Documentation:** Visit [`/docs`](/docs) for the interactive OpenAPI documentation.
    - **Endpoint:** `POST /api/verify-monument`
    """)
    # Register the @spaces.GPU function with a Gradio event so the ZeroGPU startup checker detects it
    ping_input = gr.Textbox(value="ping", visible=False)
    ping_output = gr.Textbox(visible=False)
    ping_button = gr.Button("Check GPU Status")
    ping_button.click(fn=gpu_verify, inputs=[ping_input], outputs=[ping_output])

from backend.main import app as fastapi_app

# Mount Gradio onto the existing FastAPI application
app = gr.mount_gradio_app(fastapi_app, demo, path="/demo")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
