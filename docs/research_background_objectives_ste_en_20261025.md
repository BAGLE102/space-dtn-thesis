# Space DTN: Background, Motivation, Objectives, and Progress

Report date: 2026-10-25. Latest experiment date: 2026-10-21.

Writing status: ASD-STE100-based draft for descriptive writing. Full dictionary compliance remains unverified.

<!-- REVIEW_START -->
## 1. Background

Space networks do not always provide a continuous path from a source node to a destination node. Delay-Tolerant Networking (DTN) supports data transfer across these periods without a continuous path. Nodes keep data until a contact becomes available.

In this study, a bundle is the unit of data that the routing method must transfer. Each contact has a sender, a receiver, a time window, a data rate, and a propagation delay. A Contact Plan describes these contacts.

The study treats each bundle as a whole unit. The method cannot divide a bundle between contacts on the same hop. A node must receive the complete bundle before it can send the bundle to the next node.

Each node has a buffer limit. Earlier bundles can use contact time and buffer space that a later bundle also needs. Thus, the method must use the current resource reservations when it plans a route.

## 2. Motivation

Enough total contact capacity does not mean that a continuous transmission slot is available. A contact can contain a free slot that starts after an occupied slot. The method must find a slot long enough to send the complete bundle.

Enough buffer space at full arrival does not prove that reception is feasible. The buffer limit must hold throughout reception. The same limit must hold while the node keeps or sends the bundle.

An early arrival can require a wait through a period with insufficient buffer space. A later arrival can avoid that period. Thus, arrival time alone does not show that one label can replace another label.

Earlier drafts tested transmission start times on a time grid. The current candidate uses feasible start intervals instead. This change removes the need to create a label for each time-grid point.

## 3. Relation to Existing Work

The literature review found strong overlap with an existing study. That study uses contact splitting, buffer forecasts, and contact-sequence restrictions. It also plans bundles one at a time and updates resource reservations.

These features cannot support a claim that this study introduces a new method. The research must identify a specific difference and test that difference. One candidate difference concerns the cost of resource calculations.

## 4. Objectives

The main objective is to find the earliest feasible arrival for each bundle under existing resource reservations. The output must include the route and the transmission start time on each contact.

First, the study will define consistent time, contact capacity, and buffer constraints. These definitions must distinguish contact availability from the buffer space that a receiver needs.

Second, the study will determine feasible start intervals without time-grid enumeration. Each interval must satisfy the contact window and the applicable resource limits.

Third, the study will test whether the search retains all necessary route candidates. A complete route must satisfy the buffer limit during reception, storage, and transmission. The method must distinguish an incomplete search from a search that proves no feasible route exists.

Fourth, the study will compare methods under the same model and input data. The comparison will include arrival time, calculation time, memory use, and failure cases.

An additional candidate objective is to reduce repeated resource calculations. The candidate calculates intervals on demand and reuses valid results. The study has not established this candidate as a new research contribution.

## 5. Current Progress

The project has a candidate label definition and route-search flow. Fixed route examples support the explanations in the current presentation. The complete candidate search does not yet have a verified implementation.

The project has a separate interval component for continuous buffer curves. Nine analytical cases matched their expected interval results. The tests found no differences across 9,307 fixed-start comparisons and 22,320 cache-answer comparisons.

These checks do not prove that the complete route search is correct. The component experiment used 96 contacts and five resource snapshots. Each strategy had seven timed runs.

For the local-update case with 10% contact queries, the on-demand median was 28.443 milliseconds. The full incremental strategy required 228.056 milliseconds. Both values represent the total time across five snapshots.

When queries covered all contacts, the on-demand strategy had no consistent time advantage. These results support only a conditional component benefit. The experiment did not compare the candidate with the published algorithm.

## 6. Scope and Open Questions

The current route model plans one bundle at a time in a fixed order. The model assumes known contacts and resource reservations. The model does not optimize all bundles together.

The component experiment excludes predecessor waiting, occupancy jumps, and full-route resource updates. The experiment also excludes random contact failures and shared-radio constraints. Thus, the results do not establish operational performance or complete-search optimality.

The research contribution remains unconfirmed. The next validation step is to measure resource queries during a complete search. That measurement must determine whether on-demand calculation reduces total route-planning time.
<!-- REVIEW_END -->

## Technical Terms

| Term | Meaning in this report |
|---|---|
| Space DTN | A space network that uses Delay-Tolerant Networking. |
| bundle | The complete data unit that this route model transfers without fragmentation. |
| contact | A directed transmission opportunity with a specified time window, data rate, and propagation delay. |
| Contact Plan | A description of the available contacts. |
| contact capacity | The data volume that a contact permits under the selected capacity model. |
| transmission slot | One continuous time interval for transmission on a contact. |
| buffer occupancy | The amount of data that occupies node storage at a specified time. |
| resource reservation | An accepted allocation of contact time, capacity, or buffer space. |
| feasible start interval | An interval of transmission start times that satisfies the stated resource conditions. |
| label | A candidate route state with information for further search and route reconstruction. |
| predecessor | The previous label in the candidate route. |
| snapshot | A fixed resource state for one query round in the component experiment. |
| on-demand calculation | Calculation of an interval result only when a query needs that result. |
| incremental strategy | A strategy that reuses valid results and calculates replacements after relevant resource changes. |
| cache | Stored interval results with information about their validity. |
| optimality | The earliest feasible destination arrival under the specified model and existing reservations. |

## References and Evidence

- Writing reference: [ASD-STE100 Issue 9, Section 6](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf).
- Scope and terminology: [official STEMG FAQ](https://www.asd-ste100.org/STE_faq.html).
- Existing study: Tania Alhajj and Vincent Corlay, [Improved Contact Graph Routing in Delay Tolerant Networks with Capacity and Buffer Constraints](https://arxiv.org/html/2410.15546v3), Sections III, IV, VIII, and IX.
- Candidate presentation record: [1021 candidate definitions](1021_concrete_start_intervals_ppt_20261021.md).
- Experiment evidence: [component results](demand_interval_validation_results_20261021.md) and [raw data](../output/demand_interval_validation_20261021/summary.csv).
- Writing review: [review record](research_background_objectives_ste_review_20261025.md).

This document reports existing work and candidate objectives. It does not replace the frozen algorithm specifications or approve a new algorithm.
