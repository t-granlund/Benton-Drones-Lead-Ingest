import unittest

from lead_ingest.clustering import cluster_by_radius
from lead_ingest.geo import haversine_miles
from lead_ingest.models import LeadPoint


class ClusteringTests(unittest.TestCase):
    def test_haversine_zero_for_same_point(self):
        self.assertAlmostEqual(haversine_miles(36.0, -94.0, 36.0, -94.0), 0.0)

    def test_cluster_by_radius_groups_nearby_points(self):
        points = [
            LeadPoint(1, "A", 36.3720, -94.2080),
            LeadPoint(2, "B", 36.3721, -94.2081),
            LeadPoint(3, "C", 37.0000, -95.0000),
        ]
        clusters = cluster_by_radius(points, radius_miles=0.1)
        sizes = sorted(len(cluster.members) for cluster in clusters)
        self.assertEqual(sizes, [1, 2])

    def test_cluster_empty_list(self):
        clusters = cluster_by_radius([], radius_miles=1.0)
        self.assertEqual(len(clusters), 0)

    def test_cluster_single_point(self):
        points = [LeadPoint(1, "Solo", 36.37, -94.20)]
        clusters = cluster_by_radius(points, radius_miles=1.0)
        self.assertEqual(len(clusters), 1)
        self.assertEqual(len(clusters[0].members), 1)
        self.assertEqual(clusters[0].center.name, "Solo")

    def test_cluster_all_within_radius(self):
        points = [
            LeadPoint(1, "A", 36.3720, -94.2080),
            LeadPoint(2, "B", 36.3721, -94.2081),
            LeadPoint(3, "C", 36.3722, -94.2082),
        ]
        clusters = cluster_by_radius(points, radius_miles=10.0)
        self.assertEqual(len(clusters), 1)
        self.assertEqual(len(clusters[0].members), 3)

    def test_cluster_radius_preserved_in_result(self):
        points = [LeadPoint(1, "A", 36.37, -94.20)]
        clusters = cluster_by_radius(points, radius_miles=5.5)
        self.assertEqual(clusters[0].radius_miles, 5.5)

    def test_cluster_each_cluster_has_center(self):
        points = [
            LeadPoint(1, "A", 36.3720, -94.2080),
            LeadPoint(2, "B", 36.3721, -94.2081),
            LeadPoint(3, "C", 40.0, -90.0),
        ]
        clusters = cluster_by_radius(points, radius_miles=0.01)
        for cluster in clusters:
            self.assertIsNotNone(cluster.center)
            self.assertIn(cluster.center, cluster.members)

    def test_haversine_known_distance(self):
        """Bentonville to Fayetteville is roughly 20 miles."""
        dist = haversine_miles(36.3729, -94.2088, 36.0626, -94.1574)
        self.assertGreater(dist, 15)
        self.assertLess(dist, 30)

    def test_haversine_symmetric(self):
        d1 = haversine_miles(36.0, -94.0, 37.0, -95.0)
        d2 = haversine_miles(37.0, -95.0, 36.0, -94.0)
        self.assertAlmostEqual(d1, d2)


if __name__ == "__main__":
    unittest.main()
