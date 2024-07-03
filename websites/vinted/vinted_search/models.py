from dataclasses import dataclass, field
from typing import List

__all__ = [
    'VintedSearchItem',
    'VintedSearchPage',
]

@dataclass
class VintedSearchItem:
    id: str = field(default="")
    url: str = field(default="")
    owner: str = field(default="")
    title: str = field(default="")
    subtitle: str = field(default="")
    description: str = field(default="")
    brand: str = field(default="")
    price: str = field(default="")
    size: str = field(default="")
    img_urls: List[str] = field(default_factory=list)

    @property
    def num_imgs(self) -> int:
        return len(self.img_urls)


@dataclass
class VintedSearchPage:
    page_idx: int = field(default=-1)
    items: List[VintedSearchItem] = field(default_factory=list)

    @property
    def num_items(self) -> int:
        return len(self.items)
