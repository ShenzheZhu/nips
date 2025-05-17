<div align="center">

<h1><img src="asset/payment-security.png" width="50"> The Automated but Risky Game: Modeling Agent-to-Agent Negotiations and Transactions in Consumer Markets</h1>

<p>
<a href="https://shenzhezhu.github.io">Shenzhe Zhu</a><sup>1</sup>, 
<a href="https://sunjiao123sun.github.io/">Jiao Sun</a><sup>2</sup>, 
Yi Nian<sup>3</sup>, 
<a href="https://tobin.page/">Tobin South</a><sup>4</sup>, 
<a href="https://www.media.mit.edu/people/sandy/overview/">Alex Pentland</a><sup>4,5</sup>, 
<a href="https://jiaxin-pei.github.io/">Jiaxin Pei</a><sup>5,✝</sup><br>
<sup>1</sup> University of Toronto, <sup>2</sup> Google DeepMind, <sup>3</sup> University of Southern California<br>
<sup>4</sup> Massachusetts Institute of Technology, <sup>5</sup> Stanford University<br>
(<sup>✝</sup> Corresponding Author)
</p>

<p>
<a href="#">📜 Project Page</a> | <a href="#">📝 arXiv</a>
</p>

</div>



## 📰 News
- **2025/05/17**: We have released our code and dataset.

## 📡 Overview
This repository contains the implementation of an automated negotiation system that simulates agent-to-agent negotiations in consumer markets. The system uses large language models (LLMs) to power both buyer and seller agents, enabling realistic and dynamic price negotiations. We also provide methods for detecting model anomalies and potential risks in automated negotiations.

## 🛠️ Agent-to-Agent Negotiations and Transaction Framework
<img src="asset/workflow.png" width="1000">

### Setup

1. Create a conda environment:
```bash
conda create -n negotiation python=3.9
conda activate negotiation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up API keys in a `Config.py` file:
```
OPENAI_API_KEY=your_openai_key
DEEPSEEK_API_KEY=your_deepseek_key
ZHI_API_KEY=your_zhizengzeng_key
```

### Usage

Run experiments using the provided shell script:
```bash
./run_all.sh
```

Or run individual experiments using main.py:
```bash
python main.py \
    --products-file dataset/products.json \
    --buyer-model gpt-3.5-turbo \
    --seller-model gpt-3.5-turbo \
    --summary-model gpt-3.5-turbo \
    --max-turns 30 \
    --num-experiments 1 \
    --output-dir results
```

### Budget Scenarios

The system tests five different budget scenarios for each product:
- High: Retail Price * 1.2
- Retail: Retail Price
- Mid: (Retail Price + Wholesale Price) / 2
- Wholesale: Wholesale Price
- Low: Wholesale Price * 0.8

### Supported Models
- OpenAI: GPT-4, GPT-3.5-turbo
- DeepSeek: deepseek-chat, deepseek-reasoner
- Qwen: qwen2.5-7b-instruct, qwen2.5-14b-instruct

### Results

Results are saved in the `results` directory with the following structure:
```
results/
└── seller_{seller_model}/
    └── {buyer_model}/
        └── product_{product_id}/
            └── budget_{scenario}/
                └── product_{product_id}_exp_{experiment_num}.json
```

Each result file contains:
- Complete conversation history
- Price offers
- Negotiation outcome
- Budget scenario
- Model information

We provide code for cleaning anomalous data in `data_postprocess/error_data_fix.ipynb`, which helps identify and clean abnormal cases such as DeadLock and Price Increase scenarios.

### Main Result Analysis

In `data_postprocess/draw_result.ipynb`, we provide methods for calculating various metrics and generating visualizations, including:
- Price Reduction Rate
- Total Profit
- Deal Rate
- Profit Rate

### Model Anomaly Analysis

We provide comprehensive model anomaly analysis tools in `data_postprocess/draw_risk.ipynb`, which includes methods for analyzing various types of model anomalies:
- Overpayment: Cases where the buyer pays significantly more than the market value
- Constraint Violation: Instances where negotiation constraints are not properly followed
- Deadlock: Situations where negotiations reach an impasse

## 🚀 Project Structure

```
.
├── main.py                 # Main experiment runner
├── Conversation.py         # Conversation management and negotiation logic
├── LanguageModel.py        # LLM interface and API handling
├── run_all.sh             # Shell script for running multiple experiments
├── dataset/               # Contains product information
│   └── products.json
├── results/               # Output directory for experiment results
│   └── seller_{model}/
│       └── buyer_{model}/
│           └── product_{id}/
│               └── budget_{scenario}/
├── logs/                  # Directory for experiment logs
│   └── {seller_model}_vs_{buyer_model}.log
└── data_postprocess/      # Data processing and analysis tools
    ├── error_data_fix.ipynb    # Clean anomalous data
    ├── draw_result.ipynb       # Calculate metrics and generate visualizations
    └── draw_risk.ipynb         # Model anomaly analysis
```