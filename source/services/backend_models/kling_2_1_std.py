from source.services.backend_models.base import BaseModel

class Kling21Std(BaseModel):
    POST_URL = "https://api.magnific.com/v1/ai/image-to-video/kling-v2-1-std"
    POLLING_URL = "https://api.magnific.com/v1/ai/image-to-video/kling-v2-1/{task_id}"

    @staticmethod
    def build_payload(**kwargs) -> dict:
        payload = {
            "duration": kwargs.get("duration", "5"),
            "image": kwargs["image"],
            "cfg_scale": kwargs.get("cfg_scale", 0.5)  # default sesuai dokumentasi
        }
        # Opsional
        if "prompt" in kwargs:
            payload["prompt"] = kwargs["prompt"]
        if "negative_prompt" in kwargs:
            payload["negative_prompt"] = kwargs["negative_prompt"]
        return payload