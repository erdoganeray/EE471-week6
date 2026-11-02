"""Cat-kind classifier: the pre-trained ResNet-50 from Cog's getting-started guide,
narrowed down to the five domestic cat classes of ImageNet."""
import logging
import os
import sys

# torchvision looks for the weights in ./hub (/src/hub in the image, filled by build.run in cog.yaml)
os.environ["TORCH_HOME"] = "."

import torch
from cog import BaseRunner, Input, Path
from PIL import Image
from torchvision import models

WEIGHTS = models.ResNet50_Weights.IMAGENET1K_V1
CATEGORIES = WEIGHTS.meta["categories"]

# ImageNet's domestic cat classes (big cats like lynx or tiger are left out)
CAT_BREEDS = ["tabby", "tiger cat", "Persian cat", "Siamese cat", "Egyptian cat"]
CAT_INDICES = [CATEGORIES.index(name) for name in CAT_BREEDS]

# If the five cat classes together get less than this, the photo is reported as "not a cat"
CAT_THRESHOLD = 0.2

# Every prediction is written to stdout (docker logs) and to this file (docker exec ... tail -f)
LOG_FILE = os.getenv("PREDICTION_LOG", "/tmp/predictions.log")


def create_logger():
    logger = logging.getLogger("cat-classifier")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    for handler in (logging.StreamHandler(sys.stdout), logging.FileHandler(LOG_FILE)):
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


class Runner(BaseRunner):
    def setup(self):
        """Load the model once when the container starts, not on every prediction"""
        self.log = create_logger()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = models.resnet50(weights=WEIGHTS).to(self.device)
        self.model.eval()
        self.transform = WEIGHTS.transforms()
        self.log.info("Model loaded on %s", self.device)

    def run(self, image: Path = Input(description="Photo of a cat")) -> dict:
        """Return the cat breed, the probability of each breed and the model's top 5 ImageNet classes"""
        img = Image.open(image).convert("RGB")

        # no_grad: inference only, so PyTorch doesn't keep the data needed for training
        with torch.no_grad():
            logits = self.model(self.transform(img).unsqueeze(0).to(self.device))
        probabilities = logits[0].softmax(0)

        cat_score = probabilities[CAT_INDICES].sum().item()
        # Breed probabilities relative to each other, so they add up to 1.
        # Lists instead of dicts: Cog sorts JSON object keys alphabetically, a list keeps the ranking.
        breeds = sorted(
            ({"label": name, "probability": probabilities[index].item() / cat_score}
             for name, index in zip(CAT_BREEDS, CAT_INDICES)),
            key=lambda breed: breed["probability"],
            reverse=True,
        )
        best = breeds[0]
        is_cat = cat_score >= CAT_THRESHOLD

        top5 = probabilities.topk(5)
        top_predictions = [
            {"label": CATEGORIES[i], "probability": p.item()} for p, i in zip(top5.values, top5.indices)
        ]

        self.log.info(
            "size=%dx%d cat_score=%.3f breed=%s confidence=%.3f top1=%s",
            img.width, img.height, cat_score, best["label"] if is_cat else "-",
            best["probability"] if is_cat else 0, top_predictions[0]["label"],
        )

        return {
            "is_cat": is_cat,
            "breed": best["label"] if is_cat else None,
            "confidence": best["probability"] if is_cat else None,
            "cat_score": cat_score,
            "breeds": breeds,
            "top_predictions": top_predictions,
        }
