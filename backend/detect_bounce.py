def detect_bounce(y_coords):
    if len(y_coords) < 3:
        return False
    # Image Y increases downwards
    dy1 = y_coords[-2] - y_coords[-3]
    dy2 = y_coords[-1] - y_coords[-2]
    return dy1 > 0 and dy2 <= 0


def get_scoring_side(ball_x, table_center_x):
    return 'teamA' if ball_x < table_center_x else 'teamB'
