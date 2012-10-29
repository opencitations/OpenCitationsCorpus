package neo4jHelper;

import java.util.HashMap;
import java.util.Map.Entry;

import org.neo4j.graphdb.Direction;
import org.neo4j.graphdb.GraphDatabaseService;
import org.neo4j.graphdb.Node;
import org.neo4j.graphdb.Relationship;
import org.neo4j.graphdb.Transaction;
import org.neo4j.graphdb.index.Index;
import org.neo4j.index.lucene.ValueContext;
import org.neo4j.kernel.EmbeddedGraphDatabase;

import utils.Parallelizer;

/**
 * this is a small hack which helps to calculate page rank values for rather
 * small graphs iteratively. I am sure a modern computer should be able to
 * handle graphs with about 1 Mio. nodes
 * 
 * for the sake of simpleness this is not the original algoirthm but the results
 * will be close ther is no support for calculating pagerank only on certain
 * relationship types. This might be added soon
 * 
 * @author rpickhardt
 * 
 */

public class CalculatePageRank {
	private EmbeddedGraphDatabase db;

	public EmbeddedGraphDatabase getGraphDb() {
		return db;
	}

	public void setGraphDb(EmbeddedGraphDatabase db) {
		this.db = db;
	}

	private Double d;

	public CalculatePageRank(EmbeddedGraphDatabase db2) {
		db = db2;
		d = 0.85;
	}

	CalculatePageRank(String path) {
		db = new EmbeddedGraphDatabase(path);
		d = 0.85;
	}

	public void dcalculatePageRank(Double _d, int iterationen) {
		d = _d;
		HashMap<Long, Double> nodeIndex = getNodesToIndex();
		HashMap<Long, Double> newPageRankValues = new HashMap<Long, Double>(
				nodeIndex);

		for (int i = 0; i < iterationen; i++) {
			System.out.println("iteration number: \t" + i);
			for (Long key:newPageRankValues.keySet()){
				newPageRankValues.put(key,newPageRankValues.get(key)*0.15);
			}
			
			for (Entry<Long, Double> e : nodeIndex.entrySet()) {
				Node n = db.getNodeById(e.getKey());

				int degree = 1;
				for (Relationship rel : n.getRelationships(Direction.OUTGOING)) {
					degree++;
				}

				Double currentPageRank = e.getValue();
				// this amout of PR is given to all nodes the current node links
				// to.
				Double delta = d * currentPageRank.doubleValue() / degree;

				for (Relationship rel : n.getRelationships(Direction.OUTGOING)) {
					Long otherNodeId = rel.getEndNode().getId();
					if (otherNodeId == null)
						continue;
					Double currentPRValueOfOtherNode = newPageRankValues
							.get(otherNodeId);
					newPageRankValues.put(otherNodeId,
							currentPRValueOfOtherNode + delta);
				}
			}
			nodeIndex = newPageRankValues;
		}

		updatePageRankValues(nodeIndex);

	}

	private void updatePageRankValues(HashMap<Long, Double> nodeIndex) {
		System.out.println("start to hit the disk");
		int cnt = 0;
		Transaction tx = db.beginTx();
		try {
			for (Entry<Long, Double> e : nodeIndex.entrySet()) {
				cnt++;
				if (cnt > 50000){
					tx.success();
					tx.finish();
					cnt=0;
					tx = db.beginTx();
				}
				Node n = db.getNodeById(e.getKey());
				n.setProperty("pageRankValue", e.getValue());
			}
			tx.success();
		} finally {
			tx.finish();
		}
	}

	private HashMap<Long, Double> getNodesToIndex() {
		HashMap<Long, Double> nodeIndex = new HashMap<Long, Double>();
		for (Node n : db.getAllNodes()) {
			nodeIndex.put(n.getId(), 1.0);
		}
		return nodeIndex;
	}
	
	public Index<Node> putToIndex(String indexName){
		Index<Node> searchIndex = db.index().forNodes(indexName);
		Transaction tx = db.beginTx();
		try {
			Index<Node> search = db.index().forNodes("search_idx");
			long start = System.currentTimeMillis();
			int cnt = 0;
			for (Node n:db.getAllNodes()){
				if (n.hasProperty("title") && n.hasProperty("pageRankValue")){
					searchIndex.add(n, "title", (String)n.getProperty("title"));
					searchIndex.add(n, "pr", new ValueContext((Double)n.getProperty("pageRankValue")).indexNumeric());
				}
				if (n.hasProperty("name")){
					searchIndex.add(n, "title", (String)n.getProperty("name"));
					searchIndex.add(n, "pr", new ValueContext((Double)n.getProperty("pageRankValue")).indexNumeric());
				}
				if (cnt++%5000==0){
					System.out.println(cnt);
					tx.success();
					tx.finish();
					tx = db.beginTx();
				}
			}
			tx.success();
		}finally{
			tx.finish();
		}
		return searchIndex;
	}

}
