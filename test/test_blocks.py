import asyncio
import random
import time
import unittest
from unittest.mock import patch

import pytest

import gradio as gr
from gradio.routes import PredictBody
from gradio.test_data.blocks_configs import XRAY_CONFIG
from gradio.utils import assert_configs_are_equivalent_besides_ids

pytest_plugins = ("pytest_asyncio",)


class TestBlocks(unittest.TestCase):
    maxDiff = None

    def test_set_share(self):
        with gr.Blocks() as demo:
            # self.share is False when instantiating the class
            self.assertFalse(demo.share)
            # default is False, if share is None
            demo.share = None
            self.assertFalse(demo.share)
            # if set to True, it doesn't change
            demo.share = True
            self.assertTrue(demo.share)

    @patch("gradio.utils.colab_check")
    def test_set_share_in_colab(self, mock_colab_check):
        mock_colab_check.return_value = True
        with gr.Blocks() as demo:
            # self.share is False when instantiating the class
            self.assertFalse(demo.share)
            # default is True, if share is None and colab_check is true
            demo.share = None
            self.assertTrue(demo.share)
            # if set to True, it doesn't change
            demo.share = True
            self.assertTrue(demo.share)

    def test_xray(self):
        def fake_func():
            return "Hello There"

        xray_model = lambda diseases, img: {
            disease: random.random() for disease in diseases
        }
        ct_model = lambda diseases, img: {disease: 0.1 for disease in diseases}

        with gr.Blocks() as demo:
            gr.Markdown(
                """
            # Detect Disease From Scan
            With this model you can lorem ipsum
            - ipsum 1
            - ipsum 2
            """
            )
            disease = gr.CheckboxGroup(
                choices=["Covid", "Malaria", "Lung Cancer"], label="Disease to Scan For"
            )

            with gr.Tabs():
                with gr.TabItem("X-ray"):
                    with gr.Row():
                        xray_scan = gr.Image()
                        xray_results = gr.JSON()
                    xray_run = gr.Button("Run")
                    xray_run.click(
                        xray_model, inputs=[disease, xray_scan], outputs=xray_results
                    )

                with gr.TabItem("CT Scan"):
                    with gr.Row():
                        ct_scan = gr.Image()
                        ct_results = gr.JSON()
                    ct_run = gr.Button("Run")
                    ct_run.click(
                        ct_model, inputs=[disease, ct_scan], outputs=ct_results
                    )
            textbox = gr.Textbox()
            demo.load(fake_func, [], [textbox])

        config = demo.get_config_file()
        config.pop("version")  # remove version key
        self.assertTrue(assert_configs_are_equivalent_besides_ids(XRAY_CONFIG, config))

    def test_load_from_config(self):
        def update(name):
            return f"Welcome to Gradio, {name}!"

        with gr.Blocks() as demo1:
            inp = gr.Textbox(placeholder="What is your name?")
            out = gr.Textbox()

            inp.submit(fn=update, inputs=inp, outputs=out, api_name="greet")

            gr.Image().style(height=54, width=240)

        config1 = demo1.get_config_file()
        demo2 = gr.Blocks.from_config(config1, [update])
        config2 = demo2.get_config_file()
        self.assertTrue(assert_configs_are_equivalent_besides_ids(config1, config2))

    @pytest.mark.asyncio
    async def test_async_function(self):
        async def wait():
            await asyncio.sleep(0.01)
            return True

        with gr.Blocks() as demo:
            text = gr.Textbox()
            button = gr.Button()
            button.click(wait, [text], [text])

            body = PredictBody(data=1, fn_index=0)
            start = time.time()
            result = await demo.process_api(body)
            end = time.time()
            difference = end - start
            assert difference >= 0.01
            assert result


if __name__ == "__main__":
    unittest.main()
