from dataclasses import dataclass, field
from typing import List

@dataclass
class MercariSearchItem:
    id: str = field(default="")
    url: str = field(default="")
    category: str = field(default="")
    brand: str = field(default="")
    condition: str = field(default="")
    color: str = field(default="")
    price: str = field(default="")
    status: str = field(default="")
    description: str = field(default="")
    decoration: str = field(default="")
    img_urls: List[str] = field(default_factory=list)

    @property
    def num_imgs(self) -> int:
        return len(self.img_urls)

    def __hash__(self) -> int:
        return hash(self.id)
