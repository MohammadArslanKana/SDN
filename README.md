**Hierarchical Role-Based Ensemble IDS for SDN Environments**

---

# 1️⃣ System Objective

To design and implement a **real-time, low-latency, hierarchical IDS** for Software Defined Networks (SDN) that:

* Detects attacks within 2 seconds
* Identifies attack type
* Handles multiple attack classes (SYN flood, Packet-In attack, Topology attack, etc.)
* Uses layered reasoning (fast + deep analysis)
* Maintains low inference latency (< 30ms worst case)
* Is scalable to new attack types without redesigning the architecture

---

# 2️⃣ System Overview

The IDS is composed of four logical layers:

```
SDN Traffic
   ↓
Feature Extraction (1-second stats)
   ↓
2-second Sliding Window
   ↓
Stage 1: CNN (Fast Sensor)
   ↓
Decision Gate
   ↓
Stage 2A: Transformer (Temporal Reasoner)
Stage 2B: GNN (Spatial Reasoner)
   ↓
Fusion MLP
   ↓
Final Decision + Mitigation
```
```
┌──────────────────────────┐
│   SDN Data Plane         │
│  (Mininet / Switches)    │
└───────────┬──────────────┘
            │
            ▼
┌──────────────────────────┐
│ Feature Extraction Layer │
│ (1s Time Window, Stats)  │
└───────────┬──────────────┘
            │
            ▼
┌──────────────────────────┐
│ CNN – Fast Sensor        │  ← ALWAYS RUNS
│ - Traffic morphology     │
│ - Burst detection        │
│ - Anomaly score          │
└───────────┬──────────────┘
            │
     ┌──────┴─────────┐
     │ Decision Gate  │
     │ (Confidence)   │
     └──────┬─────────┘
            │
   ┌────────┴─────────┐
   │                  │
   ▼                  ▼
┌──────────────┐   ┌──────────────┐
│ Transformer  │   │ GNN           │
│ Temporal     │   │ Spatial       │
│ Reasoner     │   │ Reasoner      │
│ (History)    │   │ (Topology)    │
└──────┬───────┘   └──────┬───────┘
       │                  │
       └────────┬─────────┘
                ▼
     ┌──────────────────────────┐
     │ Fusion / Decision Engine │
     │ - Final class            │
     │ - Confidence             │
     └──────────────────────────┘
```
---

# 3️⃣ Data Plane & Feature Layer

## 3.1 Traffic Source

* Mininet switches
* SDN controller (e.g., Ryu)
* Real-time flow statistics

## 3.2 Feature Extraction (1-second window)
```
🟢 Control Plane Metrics

packet_in_count

packet_in_rate

flow_mod_count

flow_removed_count

packet_in_to_flow_mod_ratio

🟢 Flow Table Metrics

flow_table_size

flow_table_utilization_ratio

flow_entry_growth_rate

🟢 Distribution / Entropy Metrics

unique_src_ip

unique_dst_ip

src_ip_entropy

dst_ip_entropy

🟢 Protocol Counters

tcp_syn_count

udp_packet_count

arp_packet_count

icmp_packet_count

🟢 Flow Behavior

avg_flow_duration

short_flow_ratio

🟢 Temporal / Burst

packet_in_variance

burst_score

🟢 Switch Context (for GNN)

switch_id

##attack types we will do 
Controller Flooding (Packet_In DDoS)

Flow Table Exhaustion

LOFT (Low-Rate DoS)

ARP Spoof Burst

Control-Plane Reflection Trigger
```
# 4️⃣ Stage 1 – CNN Fast Sensor (Locked)

## 4.1 Purpose

* Always running
* Provides early detection
* Lightweight
* ≤ 5ms inference

## 4.2 Input

* 2-second sliding window of extracted features

## 4.3 Output

CNN outputs three signals:

1. Binary attack confidence (Normal vs Attack)
2. Rough multi-class logits
3. 128-dimensional embedding vector

## 4.4 Design Constraints

* Shallow (2 Conv layers max)
* Embedding dimension ≤ 128
* No attention layers
* Low latency

## 4.5 Role

CNN detects:

* Traffic morphology shifts
* Burst anomalies
* Short-term attack signals

It does NOT perform final classification.

---

# 5️⃣ Decision Gate (Locked)

## 5.1 Purpose

Controls when deeper reasoning is activated.

## 5.2 Inputs

* CNN binary confidence
* Confidence threshold
* Optional anomaly spike detection

## 5.3 Output

* Whether to trust deeper modules

⚠ Transformer and GNN remain loaded but their influence is gated.

---

# 6️⃣ Stage 2A – Transformer (Temporal Reasoner)

## 6.1 Purpose

Detects:

* Persistence
* Slow attacks
* Stealth attacks
* Temporal coordination

## 6.2 Input

* Rolling buffer of last 10 CNN embeddings
* Each embedding = 2-second window
* Total history = 20 seconds

## 6.3 No Cold Start Strategy

* Transformer maintains rolling state
* Runs continuously
* Decision Gate controls influence, not execution

## 6.4 Output

Transformer outputs:

1. Refined multi-class logits
2. Temporal persistence score
3. Embedding vector (for fusion)

## 6.5 Latency Target

≤ 10–15ms

---

# 7️⃣ Stage 2B – GNN (Spatial Reasoner)

## 7.1 Purpose

Detects:

* Distributed attacks
* Cross-switch coordination
* Topology-based anomalies

## 7.2 Required Data

Must have:

* SDN topology graph
* Switch adjacency matrix
* Per-switch CNN embeddings

Graph structure:

Nodes:

* Switch IDs

Node features:

* CNN embeddings

Edges:

* Physical or logical topology links

## 7.3 Output

GNN outputs:

1. Spatial coordination score
2. Spatial multi-class logits
3. Optional embedding

## 7.4 Latency Target

≤ 15–20ms (small graph)

---

# 8️⃣ Fusion Engine (Locked)

## 8.1 Design Choice

Small learned MLP (not fixed weighted average)

## 8.2 Input Signals

Fusion receives:

* CNN binary confidence
* CNN multi-class logits
* Transformer logits
* Transformer persistence score
* GNN coordination score
* GNN logits

## 8.3 Output

* Final multi-class logits
* Final confidence score

## 8.4 Latency

≤ 1ms

---

# 9️⃣ Hierarchical Classification Strategy (Locked)

Stage 1:

* Binary detection (Normal vs Attack)

Stage 2:

* Transformer + GNN refine attack type

Fusion:

* Final multi-class decision

This improves scalability and reduces class confusion.

---

# 🔟 Latency Requirements (Locked)

Target system latency:

| Module      | Target |
| ----------- | ------ |
| CNN         | ≤ 5ms  |
| Transformer | ≤ 15ms |
| GNN         | ≤ 20ms |
| Fusion      | ≤ 1ms  |

Worst-case total: < 30–40ms

Dominant latency: 2-second detection window.

---

# 11️⃣ Training Strategy

Training is performed offline.

### CNN Training

* Multi-task:

  * Binary loss
  * Multi-class loss
* Class weighting applied

### Transformer Training

* Input: sequences of CNN embeddings
* Loss: multi-class + persistence regularization

### GNN Training

* Graph-based classification loss

### Fusion Training

* Freeze CNN/Transformer/GNN
* Train small fusion MLP

---

# 12️⃣ Real-Time Deployment Strategy

* All models loaded in memory
* Rolling buffers maintained
* No cold start
* Decision Gate controls influence, not execution
* Inference pipeline integrated with SDN controller

---

# 13️⃣ Scalability Plan

When adding new attack types:

* Update labels
* Increase num_classes
* Retrain CNN multi-class head
* Retrain Transformer + Fusion
* Architecture remains unchanged

No redesign required.

---

# 14️⃣ Design Principles Locked

* CNN = Fast morphology sensor
* Transformer = Temporal reasoner
* GNN = Spatial reasoner
* Fusion = Final judge
* No cold starts
* Low latency
* Embedding-based modular architecture
* Attack-agnostic feature design

---
