import numpy as np
import matplotlib.pyplot as plt

# Example forest size
H, W = 200, 200

# Background terrain
altitude = np.random.rand(H, W)
contour = np.random.rand(H, W)

# Predicted risk
risk = np.zeros((H, W))

def densify_path(points):
    """
    Given an array of [x, y] points, return an array containing
    every integer coordinate along the straight lines between points.
    """
    points = np.asarray(points)
    dense_points = []

    for start, end in zip(points[:-1], points[1:]):
        x1, y1 = start
        x2, y2 = end

        # Number of steps needed to cover the segment
        steps = int(max(abs(x2 - x1), abs(y2 - y1)))

        # Generate intermediate points
        for i in range(steps):
            t = i / steps
            x = round(x1 + t * (x2 - x1))
            y = round(y1 + t * (y2 - y1))

            # Avoid duplicates
            if not dense_points or dense_points[-1] != [x, y]:
                dense_points.append([x, y])

    # Add final endpoint
    if not dense_points or dense_points[-1] != list(points[-1]):
        dense_points.append(list(points[-1]))

    return np.array(dense_points)


# Example roads
roads = np.array([
    [30, 0],
    [40, 25],
    [50, 50],
    [60, 75],
    [70, 90],
    [70, 120],
    [60, 150],
    [73, 170],
    [87, 199],
])

roads = densify_path(roads)

# Example river
river = np.array([
    [80, 0],
    [75, 20],
    [72, 40],
    [68, 60],
    [80, 100],
    [100, 120],
    [130, 140],
    [150, 160],
    [199, 165],
])

river = densify_path(river)

# Illegal logging incidents
attacks = np.array([
    [40, 60],
    [36, 59],
    [62, 103],
    [54, 140],
    [75, 113],
    [39, 12],
    [79, 188],
    [78, 175],
    [48, 33],
    [67, 167],
    [163, 78],
    [153, 80],
    [167, 83],
    [166, 84],
    [158, 70],
    [9, 114],
    [183, 10],
])

def create_attack_score(attacks, W, H, sigma=10):
    attack_score = np.zeros((W, H))

    # Create coordinate grid
    x_grid, y_grid = np.meshgrid(
        np.arange(W),
        np.arange(H),
        indexing="ij"
    )

    for x, y in attacks:
        # Distance from this attack point
        distance = np.sqrt((x_grid - x)**2 + (y_grid - y)**2)

        # Gaussian decay
        score = np.exp(-(distance**2) / (2 * sigma**2))

        # Keep the maximum influence if attacks overlap
        attack_score = np.maximum(attack_score, score)

    return attack_score

attack_score = create_attack_score(attacks, W, H)

def create_attack_strength(attacks, W, H, sigma=10):
    attack_strength = np.zeros((W, H))

    # Create coordinate grid
    x_grid, y_grid = np.meshgrid(
        np.arange(W),
        np.arange(H),
        indexing="ij"
    )

    for x, y in attacks:
        # Distance from this attack point
        distance = np.sqrt((x_grid - x)**2 + (y_grid - y)**2)

        # Gaussian decay
        score = np.exp(-(distance**2) / (2 * sigma**2))

        # Keep the maximum influence if attacks overlap
        attack_strength += score

    attack_strength = (attack_strength - attack_strength.min()) / (attack_strength.max() - attack_strength.min())

    return attack_strength

attack_strength = create_attack_strength(attacks, W, H)

def get_distance_to_road(x, y):
    # Vectorized distance calculation
    diff = roads - np.array([x, y])
    distances = np.linalg.norm(diff, axis=1)
    return np.min(distances)

INPUT_FEATURES = 6
def get_cell_attribute(x, y):
    cell_altitude = altitude[x, y]
    cell_contour = contour[x, y]
    cell_road = [x, y] in roads
    cell_river = [x, y] in river
    cell_attack_strength = attack_strength[x, y]

    norm_x = x / W
    norm_y = y / H
    dist_to_road = get_distance_to_road(x, y) / (np.sqrt(W ** 2 + H ** 2))

    return np.array([
        # cell_altitude,
        # cell_contour,
        cell_river,
        cell_road,
        norm_x,
        norm_y,
        dist_to_road,
        cell_attack_strength
    ])

def get_cell_attack(x, y):
    return np.array([attack_score[x,y]])

if __name__=="__main__":
    fig, ax = plt.subplots(figsize=(8,8))

    # Background terrain
    # ax.imshow(altitude, cmap='terrain', origin='lower')

    # Risk heatmap
    ax.imshow(
        attack_score.transpose(),
        cmap='Reds',
        alpha=0.45,      # transparency
        origin='lower'
    )

    # Road
    ax.plot(
        roads[:,0],
        roads[:,1],
        color='black',
        linewidth=2,
        label='Road'
    )

    # River
    ax.plot(
        river[:,0],
        river[:,1],
        color='blue',
        linewidth=2,
        label='River'
    )

    # Logging attacks
    ax.scatter(
        attacks[:,0],
        attacks[:,1],
        marker='^',
        color='red',
        s=120,
        label='Attack',
        edgecolors='black',
    )

    ax.set_title("Forest Risk Map")
    ax.legend()
    plt.show()