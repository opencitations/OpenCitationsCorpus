from collections import defaultdict

from compare import compare

class DistanceCache(defaultdict):
    def __missing__(self, key):
        if key[0] > key[1]:
            return self[(key[1], key[0])]
        distance = compare(*key)
        self[key] = distance
        return distance

def recluster(cluster):
    cluster = set(cluster)
    distances = DistanceCache()

    new_clusters = []
    while cluster:
        current_distances = dict((article, float('inf')) for article in cluster)
        current_distances[cluster.pop()] = 0
        new_cluster = set()
        while current_distances:
            distance, selected = min((b,a) for (a,b) in current_distances.iteritems())
            if distance > 0.4:
                break
            new_cluster.add(selected)
            del current_distances[selected]
            current_distances.update((
                a, min(current_distances[a],
                       distance+distances[(a, selected)])
                ) for a in current_distances)

        new_clusters.append(new_cluster)
        cluster -= new_cluster
    return new_clusters

