from dataclasses import dataclass
from io import BytesIO
from typing import Literal

import numpy as np
import plotly.graph_objects as go
import requests
import streamlit as st
from PIL import Image, ImageDraw

from streamlit_extras import extra


@dataclass
class ImageSelector:
    image: Image.Image
    selection_type: Literal["lasso", "box"]

    @property
    def image_array(self):
        return np.array(self.image)

    @extra
    def show(self, width: int = 300, height: int = 300) -> dict:
        """
        Show the image, and enable the user to select an area in
        the image using the selection type chosen in self.selection_type.

        Args:
            width (int, optional): Width of the image container. Defaults to 300.
            height (int, optional): Height of the image container. Defaults to 300.

        Returns:
            dict: The selection coordinates
        """

        fig = go.Figure().add_trace(go.Image(z=self.image))

        if self.selection_type == "lasso":
            dragmode = "lasso"
        elif self.selection_type == "box":
            dragmode = "select"

        fig.update_layout(
            dragmode=dragmode,
            xaxis=dict(showticklabels=False),  # hide x-axis ticks
            yaxis=dict(showticklabels=False),  # hide y-axis ticks
            margin=dict(
                t=0,
                b=5,
            ),
            width=width,
            height=height,
        )

        config = {
            "displaylogo": False,
            "displayModeBar": False,
        }

        self.selection = st.plotly_chart(fig, on_select="rerun", config=config)
        return self.selection

    @extra
    def show_selection(self) -> None:
        """Shows the active image selection."""
        if coordinates := self.selection["selection"].get("box"):
            x_min, x_max = coordinates[0]["x"]
            y_min, y_max = coordinates[0]["y"]

            selection_img = self.image_array[
                int(y_min) : int(y_max), int(x_min) : int(x_max)
            ]
            st.image(selection_img)

        elif coordinates := self.selection["selection"].get("lasso"):
            lasso_x, lasso_y = coordinates[0]["x"], coordinates[0]["y"]
            # Create a white background image

            img = self.image_array
            white_background = np.ones_like(self.image_array) * 255

            # Convert image and coordinates to PIL
            img_pil = Image.fromarray((img).astype(np.uint8))
            mask = Image.new("L", (img.shape[1], img.shape[0]), 0)
            draw = ImageDraw.Draw(mask)
            polygon = list(zip(lasso_x, lasso_y))
            draw.polygon(polygon, outline=1, fill=1)
            mask_array = np.array(mask)

            # Extract the pixels within the lasso selection
            selected_pixels = np.array(img_pil)
            white_background[mask_array == 1] = selected_pixels[mask_array == 1]

            # Extract the bounding box of the polygon
            min_x, min_y = int(min(lasso_x)), int(min(lasso_y))
            max_x, max_y = int(max(lasso_x)), int(max(lasso_y))
            selection_img = Image.fromarray(
                white_background.astype(np.uint8)[min_y:max_y, min_x:max_x]
            )

            # Display the result using Streamlit
            st.image(selection_img)


def example():
    response = requests.get(
        "https://images.pexels.com/photos/45201/kitty-cat-kitten-pet-45201.jpeg?auto=compress&cs=tinysrgb&dpr=1&w=500"
    )

    img = Image.open(BytesIO(response.content))

    selection_type = st.radio(
        "Selection type", ["lasso", "box"], index=0, horizontal=True
    )

    image = ImageSelector(image=img, selection_type=selection_type)
    image.show()

    if image.selection:
        st.json(image.selection, expanded=False)
        image.show_selection()


__title__ = "Image Selector"
__desc__ = """
Allows users to select an area within an image, using a lasso or a bounding
box."""
__icon__ = "🤠"
__examples__ = [example]
__author__ = "Arnaud Miribel"
__experimental_playground__ = False
__stlite__ = True
