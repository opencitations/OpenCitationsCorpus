import neo4jHelper.CalculatePageRank;
import neo4jHelper.UnderstandDatabase;

import org.neo4j.graphdb.Node;
import org.neo4j.graphdb.Relationship;
import org.neo4j.kernel.EmbeddedGraphDatabase;

import utils.Config;


public class EntryPoint {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		UnderstandDatabase ud = new UnderstandDatabase(Config.get().neo4jDbPath);
//		ud.listProperties(50);
//		ud.countAverageNodeDegrees(50);
		System.out.println("calculate pagerank with "+Config.get().pageRankIterations+" iterations");
//		CalculatePageRank cp = new CalculatePageRank(ud.getGraphDB());
//		cp.dcalculatePageRank(0.85, Config.get().pageRankIterations);
//		ud.setGraphDB(cp.getGraphDb());
//		ud.showPageRankValues();
		ud.search("Stability conditions on K3 surfaces");
		ud.shutDown();
		
	}

}
