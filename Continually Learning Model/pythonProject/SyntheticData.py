import numpy as np
import matplotlib.pyplot as plt

# Example forest size
H, W = 200, 200

# Background terrain
altitude = np.random.rand(H, W)
contour = np.random.rand(H, W)

# Predicted risk
risk = np.zeros((H, W))

# Example roads
roads = np.array([
    [0, 30],
    [25, 40],
    [50, 50],
    [75, 60],
    [90, 70],
    [120, 70],
    [150, 60],
    [170, 73],
    [199, 87],
])

# Example river
river = np.array([
    [0, 80],
    [20, 75],
    [40, 72],
    [60, 68],
    [100, 80],
    [120, 100],
    [140, 130],
    [160, 150],
    [165, 199],
])


# Illegal logging incidents
attacks = np.array([
    [60, 40],
    [45, 75],
    [70, 80]
])

def get_cell_attribute(x, y):
    cell_altitude = altitude[x, y]
    cell_contour = contour[x, y]
    cell_attack = [x,y] in attacks
    cell_road = [x, y] in roads
    cell_river = [x, y] in river

    return np.array([cell_altitude, cell_contour, cell_attack, cell_river, cell_road])

if __name__=="__main__":
    fig, ax = plt.subplots(figsize=(8,8))

    # Background terrain
    # ax.imshow(altitude, cmap='terrain', origin='lower')

    # Risk heatmap
    ax.imshow(
        risk,
        cmap='Reds',
        alpha=0.45,      # transparency
        origin='lower'
    )

    # Road
    ax.plot(
        roads[:,1],
        roads[:,0],
        color='black',
        linewidth=2,
        label='Road'
    )

    # River
    ax.plot(
        river[:,1],
        river[:,0],
        color='blue',
        linewidth=2,
        label='River'
    )

    # Logging attacks
    ax.scatter(
        attacks[:,1],
        attacks[:,0],
        marker='^',
        color='red',
        s=120,
        label='Attack',
        edgecolors='black',
    )

    ax.set_title("Forest Risk Map")
    ax.legend()
    plt.show()