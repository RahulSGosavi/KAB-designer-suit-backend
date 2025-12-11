from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import google.generativeai as genai
from app.routers.gemini import generate_leonardo_image, GEMINI_API_KEY

router = APIRouter()

# Reuse the same Gemini configuration
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")
GEMINI_DISABLED = True  # hard-disable Gemini to avoid 404s/noise
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

FALLBACK_MODELS = [
    GEMINI_MODEL,
    "gemini-2.0-pro-exp",
    "gemini-1.5-pro-latest",
    "gemini-1.5-flash-latest",
    "gemini-pro",
]

def get_gemini_model():
    return None  # Gemini intentionally disabled


class GenerateRequest(BaseModel):
    prompt: str
    variants: int = 3
    projectId: Optional[str] = None
    generateAllViews: bool = False  # Generate front, left, right, top views together


class UploadRequest(BaseModel):
    name: str
    type: str = "pdf"


@router.post("/generate")
async def generate_design(req: GenerateRequest):
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required")

    variants_to_create = max(1, min(req.variants or 1, 3))

    model = get_gemini_model()
    results: List[dict] = []

    for idx in range(variants_to_create):
        enhanced_prompt = req.prompt.strip()
        image_urls = []
        image_error: Optional[str] = None

        # Gemini enhancement is disabled; use raw prompt
        enhanced_prompt = req.prompt.strip()

        try:
            # Generate front view
            leonardo_result = generate_leonardo_image(enhanced_prompt)
            front_image_urls = leonardo_result.get("image_urls", [])
            image_urls.extend(front_image_urls)
            
            # If generateAllViews is True, generate all angles at once for consistency
            if req.generateAllViews and front_image_urls:
                view_prompts = [
                    (enhanced_prompt + ". EXACT SAME DESIGN from left side perspective, camera positioned to the left showing the side view of the same layout, same cabinets, same colors, same materials, same appliances, only camera angle changed to left side."),
                    (enhanced_prompt + ". EXACT SAME DESIGN from right side perspective, camera positioned to the right showing the side view of the same layout, same cabinets, same colors, same materials, same appliances, only camera angle changed to right side."),
                    (enhanced_prompt + ". EXACT SAME DESIGN from top-down bird's eye view, aerial perspective from above showing the same layout, same cabinets, same colors, same materials, same appliances, only camera angle changed to top view.")
                ]
                
                for view_prompt in view_prompts:
                    try:
                        view_result = generate_leonardo_image(view_prompt)
                        view_images = view_result.get("image_urls", [])
                        if view_images:
                            image_urls.extend(view_images)
                    except Exception:
                        # If one view fails, continue with others
                        pass
                        
            image_status = leonardo_result.get("status")
        except HTTPException as e:
            image_error = e.detail if isinstance(e.detail, str) else str(e.detail)
            image_status = "error"
        except Exception as e:
            image_error = str(e)
            image_status = "error"

        results.append(
            {
                "id": f"variant-{idx+1}",
                "title": f"Variant {idx+1}",
                "enhanced_prompt": enhanced_prompt,
                "image_urls": image_urls,
                "status": image_status,
                "image_error": image_error,
            }
        )

    return {"success": True, "variants": results}


@router.post("/upload")
async def upload_placeholder(req: UploadRequest):
    # Implementation for uploads will be added later.
    return {"message": "upload stub", "name": req.name, "type": req.type}


@router.get("/history")
async def history():
    # Will return recent prompts/variants.
    return {"items": []}

