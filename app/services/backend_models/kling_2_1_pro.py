from app.services.backend_models.base import BaseModel

class Kling21Pro(BaseModel):
    POST_URL = "https://api.magnific.com/v1/ai/image-to-video/kling-v2-1-pro"
    POLLING_URL = "https://api.magnific.com/v1/ai/image-to-video/kling-v2-1/{task_id}"

    @staticmethod
    def build_payload(**kwargs) -> dict:
        payload = {
            "duration": kwargs.get("duration", "5"),
            "image": kwargs["image"],
            "cfg_scale": kwargs.get("cfg_scale", 0.5)  # default sesuai dokumentasi
        }
        if "image_tail" in kwargs:
            payload["image_tail"] = kwargs["image_tail"]
        if "prompt" in kwargs:
            payload["prompt"] = kwargs["prompt"]
        if "negative_prompt" in kwargs:
            payload["negative_prompt"] = kwargs["negative_prompt"]
        return payload