import neo4jHelper.UnderstandDatabase;

import org.neo4j.graphdb.Node;
import org.neo4j.graphdb.Relationship;
import org.neo4j.kernel.EmbeddedGraphDatabase;


public class EntryPoint {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		UnderstandDatabase ud = new UnderstandDatabase("/var/lib/datasets/rawdata/relatedwork/db_folder");
//		ud.listProperties(50);
		ud.countAverageNodeDegrees(50);
		System.out.println("here we go");

		ud.shutDown();
		
	}

}
