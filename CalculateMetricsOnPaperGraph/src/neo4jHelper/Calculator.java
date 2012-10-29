package neo4jHelper;

import org.neo4j.kernel.EmbeddedGraphDatabase;

public class Calculator {

	protected EmbeddedGraphDatabase graphDB;

	public Calculator() {
		super();
	}

	public EmbeddedGraphDatabase getGraphDB() {
		return graphDB;
	}

	public void setGraphDB(EmbeddedGraphDatabase graphDB) {
		this.graphDB = graphDB;
	}


}