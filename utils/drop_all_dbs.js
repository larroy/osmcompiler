var dbs = db.getMongo().getDBNames()
for(var i in dbs) {
    db = db.getMongo().getDB(dbs[i]);
    print("dropping database: " + db.getName());
    db.dropDatabase();
}
