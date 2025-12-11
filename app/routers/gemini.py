# backend/app/routers/gemini.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import time
import requests
import google.generativeai as genai
import base64
from io import BytesIO

router = APIRouter()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")
GEMINI_DISABLED = True  # hard-disable Gemini to avoid 404s/noise
FALLBACK_MODELS = [
    GEMINI_MODEL,
    "gemini-2.0-pro-exp",
    "gemini-1.5-pro-latest",
    "gemini-1.5-flash-latest",
    "gemini-pro",
]
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def get_gemini_model():
    return None  # Gemini intentionally disabled

LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY")
LEONARDO_MODEL_ID = os.getenv("LEONARDO_MODEL_ID", "1e60896f-3c26-4296-8ecc-53e2afecc132")
LEONARDO_API_URL = os.getenv("LEONARDO_API_URL", "https://cloud.leonardo.ai/api/rest/v1")

class KitchenElement(BaseModel):
    type: str
    x: float
    y: float
    width: Optional[float] = None
    height: Optional[float] = None
    furnitureType: Optional[str] = None
    fill: Optional[str] = None

class GenerateKitchenRequest(BaseModel):
    elements: List[KitchenElement]
    wallColor: str = "#FFFFFF"
    floorColor: str = "#F5F5F5"
    ceilingColor: str = "#FFFFFF"
    kitchenShape: Optional[str] = None  # 'l-shape', 'u-shape', 'galley', etc.
    generateImage: bool = False

def convertDesignToPrompt(elements: List[KitchenElement], wallColor: str, floorColor: str, ceilingColor: str, kitchenShape: Optional[str]) -> str:
    """Convert design elements to a descriptive prompt for Gemini"""
    
    # Detect kitchen shape from elements
    walls = [e for e in elements if e.type == 'wall']
    baseCabinets = [e for e in elements if e.furnitureType in ['base-cabinet', 'cabinet']]
    wallCabinets = [e for e in elements if e.furnitureType == 'wall-cabinet']
    sinks = [e for e in elements if e.furnitureType == 'sink']
    stoves = [e for e in elements if e.furnitureType == 'stove']
    refrigerators = [e for e in elements if e.furnitureType == 'refrigerator']
    
    # Build description
    shape_desc = kitchenShape or "modern"
    if len(walls) >= 3:
        if kitchenShape:
            shape_desc = f"{kitchenShape} kitchen"
        else:
            shape_desc = "U-shaped kitchen" if len(walls) == 3 else "L-shaped kitchen"
    
    # Color descriptions
    color_map = {
        "#FFFFFF": "white", "#F5F5F5": "light gray", "#E5E7EB": "gray",
        "#B68A5A": "warm wood", "#2B2F36": "dark", "#7CAB6A": "green",
        "#2F6F9F": "blue", "#D2691E": "wood", "#8B7355": "brown"
    }
    wall_color_name = color_map.get(wallColor, "white")
    floor_color_name = color_map.get(floorColor, "light gray")
    
    # Cabinet description
    cabinet_color = "light wood" if baseCabinets else "white"
    if baseCabinets:
        first_cabinet = baseCabinets[0]
        if first_cabinet.fill:
            cabinet_color = color_map.get(first_cabinet.fill, "light wood")
    
    prompt = f"""Create a photorealistic, professional interior design rendering of a {shape_desc} kitchen.

Design specifications:
- Kitchen layout: {shape_desc}
- Wall color: {wall_color_name}
- Floor: {floor_color_name} flooring
- Cabinets: {cabinet_color} base cabinets and wall cabinets
- Countertops: white marble or quartz countertops sitting flat on base cabinets
- Number of base cabinets: {len(baseCabinets)}
- Number of wall cabinets: {len(wallCabinets)}
"""
    
    if sinks:
        prompt += f"- Kitchen sink: stainless steel sink integrated into countertop\n"
    if stoves:
        prompt += f"- Gas stove: black gas stove positioned flat on countertop\n"
    if refrigerators:
        prompt += f"- Refrigerator: stainless steel refrigerator\n"
    
    prompt += """
Style requirements:
- Photorealistic quality like professional interior design photography
- Natural lighting from windows
- Soft shadows and realistic materials
- Modern, clean aesthetic
- Countertops must be perfectly flat on base cabinets (not floating)
- All appliances properly integrated into the design
- Professional kitchen design magazine quality

Camera angle: Interior view from inside the kitchen, eye level perspective showing the full kitchen layout.
"""
    
    return prompt

def generate_leonardo_image(prompt: str) -> dict:
    """Create an image with Leonardo and return urls + metadata."""
    if not LEONARDO_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Leonardo API key not configured"
        )
    
    headers = {
        "Authorization": f"Bearer {LEONARDO_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    try:
        create_payload = {
            "prompt": prompt,
            "modelId": LEONARDO_MODEL_ID,
            # Leonardo accepts specific sizes; keep within 1024 range for reliability.
            "width": 1024,
            "height": 768,
            "num_images": 1,
            "guidance_scale": 7,
            "public": False,
        }
        create_resp = requests.post(
            f"{LEONARDO_API_URL}/generations",
            json=create_payload,
            headers=headers,
            timeout=30
        )
        if create_resp.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to create Leonardo generation: {create_resp.status_code} {create_resp.text}"
            )
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to create Leonardo generation: {str(e)}"
        )
    
    generation_id = create_resp.json().get("sdGenerationJob", {}).get("generationId")
    if not generation_id:
        raise HTTPException(
            status_code=502,
            detail="Leonardo generationId missing from response"
        )
    
    # Poll for completion
    deadline = time.time() + 60  # up to ~1 minute
    while time.time() < deadline:
        time.sleep(4)
        try:
            poll_resp = requests.get(
                f"{LEONARDO_API_URL}/generations/{generation_id}",
                headers=headers,
                timeout=20
            )
            poll_resp.raise_for_status()
        except requests.RequestException as e:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to fetch Leonardo generation status: {str(e)}"
            )
        
        gen_data = poll_resp.json().get("generations_by_pk") or {}
        status = (gen_data.get("status") or "").upper()
        
        if status in ["COMPLETE", "COMPLETED", "FINISHED"]:
            images = gen_data.get("generated_images") or []
            image_urls = [img.get("url") for img in images if img.get("url")]
            if not image_urls:
                raise HTTPException(
                    status_code=502,
                    detail="Leonardo generation completed without images"
                )
            return {
                "generation_id": generation_id,
                "image_urls": image_urls,
                "status": status.lower()
            }
        
        if status in ["FAILED", "ERROR"]:
            raise HTTPException(
                status_code=502,
                detail=f"Leonardo generation failed with status {status}"
            )
    
    raise HTTPException(
        status_code=504,
        detail="Leonardo generation timed out before completion"
    )

@router.post("/generate-kitchen")
async def generate_kitchen_image(request: GenerateKitchenRequest):
    """Generate a photorealistic kitchen image; Gemini enhancement is disabled."""
    
    try:
        # Convert design to prompt
        prompt = convertDesignToPrompt(
            request.elements,
            request.wallColor,
            request.floorColor,
            request.ceilingColor,
            request.kitchenShape
        )
        
        # Gemini enhancement disabled; use base prompt
        enhanced_prompt = prompt

        leonardo_result = None
        leonardo_error = None

        if request.generateImage:
            if not LEONARDO_API_KEY:
                leonardo_error = "Leonardo API key not configured"
            else:
                try:
                    leonardo_result = generate_leonardo_image(enhanced_prompt)
                except HTTPException as e:
                    leonardo_error = e.detail if isinstance(e.detail, str) else str(e.detail)
                except Exception as e:
                    leonardo_error = str(e)
        
        response_body = {
            "success": True,
            "original_prompt": prompt,
            "enhanced_prompt": enhanced_prompt,
            "message": "Prompt ready for image generation.",
        }

        if leonardo_result:
            response_body.update({
                "image_provider": "leonardo",
                "image_urls": leonardo_result.get("image_urls"),
                "generation_id": leonardo_result.get("generation_id"),
                "status": leonardo_result.get("status")
            })
        elif leonardo_error:
            response_body["image_error"] = leonardo_error
        
        return response_body
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate kitchen image: {str(e)}"
        )

@router.post("/generate-kitchen-image")
async def generate_kitchen_image_direct(request: GenerateKitchenRequest):
    """Generate kitchen image using Gemini's image generation (if available)"""
    
    if not LEONARDO_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Leonardo API key not configured"
        )
    
    try:
        prompt = convertDesignToPrompt(
            request.elements,
            request.wallColor,
            request.floorColor,
            request.ceilingColor,
            request.kitchenShape
        )
        
        image_result = generate_leonardo_image(prompt)
        
        return {
            "success": True,
            "prompt": prompt,
            "image_provider": "leonardo",
            "image_urls": image_result.get("image_urls"),
            "generation_id": image_result.get("generation_id"),
            "status": image_result.get("status")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate image: {str(e)}"
        )

