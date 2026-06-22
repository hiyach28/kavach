import networkx as nx
from sqlalchemy.orm import Session
from app.models import Campaign, Case, CaseInfraLink, InfraNode

def compute_takedown_brief(db: Session, campaign_id: int):
    # Get all cases for the campaign
    cases = db.query(Case).filter(Case.campaign_id == campaign_id).all()
    if not cases:
        return None

    case_ids = [c.id for c in cases]
    
    # Check cross_jurisdiction
    districts = {c.district for c in cases if c.district}
    cross_jurisdiction = len(districts) > 1

    # Get all infra links for these cases
    links = db.query(CaseInfraLink).filter(CaseInfraLink.case_id.in_(case_ids)).all()
    infra_ids = list({link.infra_node_id for link in links})

    if not infra_ids:
        # No infrastructure, can't target anything
        return {
            "cross_jurisdiction": cross_jurisdiction,
            "primary_target_infra_id": None,
            "primary_target_betweenness": 0.0,
            "pct_connectivity_lost": 0.0,
            "fractures_network": False
        }

    # Bipartite Graph of Cases (prefix "C_") and InfraNodes (prefix "I_")
    B = nx.Graph()
    for c in cases:
        B.add_node(f"C_{c.id}", bipartite=0)
    for i_id in infra_ids:
        B.add_node(f"I_{i_id}", bipartite=1)
    for link in links:
        B.add_edge(f"C_{link.case_id}", f"I_{link.infra_node_id}")

    # Compute betweenness centrality on the bipartite graph
    betweenness = nx.betweenness_centrality(B)
    
    # Filter to only Infra nodes
    infra_betweenness = {k: v for k, v in betweenness.items() if k.startswith("I_")}
    if not infra_betweenness:
        return {
            "cross_jurisdiction": cross_jurisdiction,
            "primary_target_infra_id": None,
            "primary_target_betweenness": 0.0,
            "pct_connectivity_lost": 0.0,
            "fractures_network": False
        }

    # Highest value target
    best_target = max(infra_betweenness.items(), key=lambda x: x[1])
    target_node = best_target[0]
    target_score = best_target[1]
    primary_target_infra_id = int(target_node.split("_")[1])

    # Compute Case-to-Case graph connectivity before removal
    def get_case_graph(bipartite_graph):
        CG = nx.Graph()
        c_nodes = [n for n, d in bipartite_graph.nodes(data=True) if d.get('bipartite') == 0]
        CG.add_nodes_from(c_nodes)
        
        i_nodes = [n for n, d in bipartite_graph.nodes(data=True) if d.get('bipartite') == 1]
        for i_node in i_nodes:
            neighbors = list(bipartite_graph.neighbors(i_node))
            for i in range(len(neighbors)):
                for j in range(i + 1, len(neighbors)):
                    CG.add_edge(neighbors[i], neighbors[j])
        return CG

    CG_before = get_case_graph(B)
    num_components_before = nx.number_connected_components(CG_before)
    edges_before = CG_before.number_of_edges()

    # Remove the target and recompute
    B_after = B.copy()
    B_after.remove_node(target_node)
    CG_after = get_case_graph(B_after)
    
    num_components_after = nx.number_connected_components(CG_after)
    edges_after = CG_after.number_of_edges()

    fractures_network = num_components_after > num_components_before
    pct_connectivity_lost = 0.0
    if edges_before > 0:
        pct_connectivity_lost = float(edges_before - edges_after) / edges_before

    return {
        "cross_jurisdiction": cross_jurisdiction,
        "primary_target_infra_id": primary_target_infra_id,
        "primary_target_betweenness": target_score,
        "pct_connectivity_lost": pct_connectivity_lost,
        "fractures_network": fractures_network
    }
