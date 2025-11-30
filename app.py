from flask import Flask, send_from_directory, jsonify, request
import json
import os
import hashlib
import random
from datetime import datetime, timezone
from sympy import symbols, integrate, sin, cos, exp, ln, sqrt, pi, sympify, simplify, diff, N, Rational, latex
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

app = Flask(__name__)

LEADERBOARD_FILE = 'leaderboard.json'
DAILY_QUESTIONS_FILE = 'daily_questions.json'
USER_ATTEMPTS_FILE = 'user_attempts.json'

x = symbols('x')

def get_today_string():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d')

def get_seeded_random(difficulty):
    today = get_today_string()
    seed_string = f"{today}:{difficulty}"
    seed = int(hashlib.sha256(seed_string.encode()).hexdigest(), 16) % (2**32)
    return random.Random(seed)

def generate_easy_question(rng):
    templates = [
        lambda: generate_linear_definite(rng),
        lambda: generate_quadratic_definite(rng),
        lambda: generate_simple_power_definite(rng),
    ]
    return rng.choice(templates)()

def generate_linear_definite(rng):
    a = rng.randint(1, 5)
    b = rng.randint(-3, 5)
    lower = rng.randint(0, 3)
    upper = rng.randint(lower + 1, lower + 4)
    
    integrand = a*x + b
    result = integrate(integrand, (x, lower, upper))
    
    return {
        'latex': f"\\int_{{{lower}}}^{{{upper}}} ({a}x {'+' if b >= 0 else ''}{b}) \\, dx",
        'answer': float(result),
        'answer_type': 'numeric',
        'integrand': str(integrand),
        'bounds': [lower, upper]
    }

def generate_quadratic_definite(rng):
    a = rng.randint(1, 3)
    b = rng.randint(-2, 3)
    c = rng.randint(-3, 3)
    lower = rng.randint(0, 2)
    upper = rng.randint(lower + 1, lower + 3)
    
    integrand = a*x**2 + b*x + c
    result = integrate(integrand, (x, lower, upper))
    
    terms = []
    if a != 0:
        terms.append(f"{a}x^2" if a != 1 else "x^2")
    if b != 0:
        terms.append(f"{'+' if b > 0 else ''}{b}x" if b != 1 and b != -1 else ('+x' if b == 1 else '-x'))
    if c != 0:
        terms.append(f"{'+' if c > 0 else ''}{c}")
    
    expr_str = ''.join(terms) if terms else '0'
    if expr_str.startswith('+'):
        expr_str = expr_str[1:]
    
    return {
        'latex': f"\\int_{{{lower}}}^{{{upper}}} ({a}x^2 {'+' if b >= 0 else ''}{b}x {'+' if c >= 0 else ''}{c}) \\, dx",
        'answer': float(result),
        'answer_type': 'numeric',
        'integrand': str(integrand),
        'bounds': [lower, upper]
    }

def generate_simple_power_definite(rng):
    n = rng.randint(2, 4)
    a = rng.randint(1, 3)
    lower = rng.randint(0, 2)
    upper = rng.randint(lower + 1, lower + 3)
    
    integrand = a * x**n
    result = integrate(integrand, (x, lower, upper))
    
    return {
        'latex': f"\\int_{{{lower}}}^{{{upper}}} {a}x^{n} \\, dx",
        'answer': float(result),
        'answer_type': 'numeric',
        'integrand': str(integrand),
        'bounds': [lower, upper]
    }

def generate_medium_question(rng):
    templates = [
        lambda: generate_trig_indefinite(rng),
        lambda: generate_exp_indefinite(rng),
        lambda: generate_trig_definite(rng),
    ]
    return rng.choice(templates)()

def generate_trig_indefinite(rng):
    trig_type = rng.choice(['sin', 'cos'])
    a = rng.randint(1, 3)
    b = rng.randint(1, 3)
    
    if trig_type == 'sin':
        integrand = a * sin(b*x)
        antiderivative = integrate(integrand, x)
        latex_str = f"\\int {a}\\sin({b}x) \\, dx"
    else:
        integrand = a * cos(b*x)
        antiderivative = integrate(integrand, x)
        latex_str = f"\\int {a}\\cos({b}x) \\, dx"
    
    return {
        'latex': latex_str,
        'answer': latex(antiderivative),
        'answer_symbolic': str(antiderivative),
        'answer_type': 'indefinite',
        'integrand': str(integrand)
    }

def generate_exp_indefinite(rng):
    a = rng.randint(1, 3)
    b = rng.randint(1, 3)
    
    integrand = a * exp(b*x)
    antiderivative = integrate(integrand, x)
    
    return {
        'latex': f"\\int {a}e^{{{b}x}} \\, dx",
        'answer': latex(antiderivative),
        'answer_symbolic': str(antiderivative),
        'answer_type': 'indefinite',
        'integrand': str(integrand)
    }

def generate_trig_definite(rng):
    trig_type = rng.choice(['sin', 'cos'])
    a = rng.randint(1, 3)
    
    bounds_options = [
        (0, 'pi/2', 0, pi/2),
        (0, 'pi', 0, pi),
        ('pi/6', 'pi/3', pi/6, pi/3),
        ('pi/4', 'pi/2', pi/4, pi/2),
    ]
    lower_str, upper_str, lower_val, upper_val = rng.choice(bounds_options)
    
    if trig_type == 'sin':
        integrand = a * sin(x)
        latex_str = f"\\int_{{{lower_str}}}^{{{upper_str}}} {a}\\sin(x) \\, dx"
    else:
        integrand = a * cos(x)
        latex_str = f"\\int_{{{lower_str}}}^{{{upper_str}}} {a}\\cos(x) \\, dx"
    
    result = integrate(integrand, (x, lower_val, upper_val))
    
    return {
        'latex': latex_str,
        'answer': float(N(result)),
        'answer_exact': latex(result),
        'answer_type': 'numeric',
        'integrand': str(integrand),
        'bounds': [str(lower_val), str(upper_val)]
    }

def generate_hard_question(rng):
    templates = [
        lambda: generate_integration_by_parts(rng),
        lambda: generate_u_substitution(rng),
        lambda: generate_trig_product(rng),
    ]
    return rng.choice(templates)()

def generate_integration_by_parts(rng):
    ibp_type = rng.choice(['x_exp', 'x_sin', 'x_cos', 'x_ln'])
    a = rng.randint(1, 2)
    
    if ibp_type == 'x_exp':
        integrand = a * x * exp(x)
        antiderivative = integrate(integrand, x)
        latex_str = f"\\int {a}x \\cdot e^x \\, dx"
    elif ibp_type == 'x_sin':
        integrand = a * x * sin(x)
        antiderivative = integrate(integrand, x)
        latex_str = f"\\int {a}x \\cdot \\sin(x) \\, dx"
    elif ibp_type == 'x_cos':
        integrand = a * x * cos(x)
        antiderivative = integrate(integrand, x)
        latex_str = f"\\int {a}x \\cdot \\cos(x) \\, dx"
    else:
        integrand = a * x * ln(x)
        antiderivative = integrate(integrand, x)
        latex_str = f"\\int {a}x \\cdot \\ln(x) \\, dx"
    
    return {
        'latex': latex_str,
        'answer': latex(antiderivative),
        'answer_symbolic': str(antiderivative),
        'answer_type': 'indefinite',
        'integrand': str(integrand)
    }

def generate_u_substitution(rng):
    sub_type = rng.choice(['exp_squared', 'sin_cos', 'power_chain'])
    
    if sub_type == 'exp_squared':
        a = rng.randint(1, 2)
        integrand = a * x * exp(x**2)
        antiderivative = integrate(integrand, x)
        latex_str = f"\\int {a}x \\cdot e^{{x^2}} \\, dx"
    elif sub_type == 'sin_cos':
        n = rng.randint(2, 3)
        integrand = sin(x)**n * cos(x)
        antiderivative = integrate(integrand, x)
        latex_str = f"\\int \\sin^{n}(x) \\cdot \\cos(x) \\, dx"
    else:
        a = rng.randint(1, 3)
        b = rng.randint(1, 2)
        integrand = a * (2*x + b) * (x**2 + b*x)**2
        antiderivative = integrate(integrand, x)
        latex_str = f"\\int {a}(2x+{b})(x^2+{b}x)^2 \\, dx"
    
    return {
        'latex': latex_str,
        'answer': latex(antiderivative),
        'answer_symbolic': str(antiderivative),
        'answer_type': 'indefinite',
        'integrand': str(integrand)
    }

def generate_trig_product(rng):
    m = rng.randint(2, 3)
    n = rng.randint(1, 2)
    
    integrand = sin(x)**m * cos(x)**n
    antiderivative = integrate(integrand, x)
    
    return {
        'latex': f"\\int \\sin^{m}(x) \\cdot \\cos^{n}(x) \\, dx",
        'answer': latex(antiderivative),
        'answer_symbolic': str(antiderivative),
        'answer_type': 'indefinite',
        'integrand': str(integrand)
    }

def get_daily_questions():
    today = get_today_string()
    
    if os.path.exists(DAILY_QUESTIONS_FILE):
        with open(DAILY_QUESTIONS_FILE, 'r') as f:
            data = json.load(f)
            if data.get('date') == today:
                return data['questions']
    
    questions = {
        'easy': generate_easy_question(get_seeded_random('easy')),
        'medium': generate_medium_question(get_seeded_random('medium')),
        'hard': generate_hard_question(get_seeded_random('hard'))
    }
    
    with open(DAILY_QUESTIONS_FILE, 'w') as f:
        json.dump({'date': today, 'questions': questions}, f)
    
    return questions

def load_user_attempts():
    if os.path.exists(USER_ATTEMPTS_FILE):
        with open(USER_ATTEMPTS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_user_attempts(data):
    with open(USER_ATTEMPTS_FILE, 'w') as f:
        json.dump(data, f)

def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, 'r') as f:
            return json.load(f)
    return []

def save_leaderboard(data):
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(data, f)

def check_numeric_answer(user_answer, correct_answer, tolerance=0.01):
    try:
        user_val = float(user_answer)
        return abs(user_val - correct_answer) <= tolerance
    except:
        return False

def safe_parse_user_expr(user_answer):
    import re
    
    allowed_pattern = r'^[\d\s\+\-\*\/\^\(\)xepi\.\,sincotaglnexp]+$'
    cleaned = user_answer.lower().replace(' ', '')
    
    if not re.match(allowed_pattern, cleaned, re.IGNORECASE):
        return None
    
    dangerous_patterns = ['import', 'exec', 'eval', 'open', 'file', '__', 'lambda', 
                          'globals', 'locals', 'getattr', 'setattr', 'delattr',
                          'compile', 'dir', 'vars', 'type', 'class']
    for pattern in dangerous_patterns:
        if pattern in cleaned:
            return None
    
    safe_locals = {
        'x': x,
        'sin': sin,
        'cos': cos,
        'tan': lambda arg: sin(arg)/cos(arg),
        'exp': exp,
        'e': exp(1),
        'pi': pi,
        'ln': ln,
        'log': ln,
        'sqrt': sqrt,
    }
    
    try:
        transformations = standard_transformations + (implicit_multiplication_application,)
        expr = parse_expr(user_answer, local_dict=safe_locals, transformations=transformations, evaluate=False)
        return expr
    except:
        return None

def check_indefinite_answer(user_answer, integrand_str):
    try:
        user_expr = safe_parse_user_expr(user_answer)
        if user_expr is None:
            return False
        
        integrand = sympify(integrand_str)
        
        derivative = diff(user_expr, x)
        difference = simplify(derivative - integrand)
        
        if difference == 0:
            return True
        
        for test_val in [0.5, 1.0, 1.5, 2.0]:
            try:
                diff_val = float(N(difference.subs(x, test_val)))
                if abs(diff_val) > 0.001:
                    return False
            except:
                pass
        
        return True
    except Exception as e:
        return False

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/api/daily-questions', methods=['GET'])
def get_daily_questions_api():
    questions = get_daily_questions()
    
    safe_questions = {}
    for difficulty, q in questions.items():
        safe_questions[difficulty] = {
            'latex': q['latex'],
            'answer_type': q['answer_type']
        }
    
    return jsonify({
        'date': get_today_string(),
        'questions': safe_questions
    })

@app.route('/api/check-answer', methods=['POST'])
def check_answer():
    data = request.get_json()
    username = data.get('username', '').strip()
    difficulty = data.get('difficulty', '')
    user_answer = data.get('answer', '')
    
    if not username or not difficulty or user_answer == '':
        return jsonify({'error': 'Missing required fields'}), 400
    
    if difficulty not in ['easy', 'medium', 'hard']:
        return jsonify({'error': 'Invalid difficulty'}), 400
    
    today = get_today_string()
    attempts = load_user_attempts()
    
    user_key = username.lower()
    if user_key not in attempts:
        attempts[user_key] = {}
    if today not in attempts[user_key]:
        attempts[user_key][today] = {}
    
    if difficulty in attempts[user_key][today]:
        return jsonify({
            'error': 'Already attempted',
            'already_attempted': True,
            'was_correct': attempts[user_key][today][difficulty]['correct']
        })
    
    questions = get_daily_questions()
    question = questions[difficulty]
    
    is_correct = False
    if question['answer_type'] == 'numeric':
        is_correct = check_numeric_answer(user_answer, question['answer'])
    else:
        is_correct = check_indefinite_answer(user_answer, question['integrand'])
    
    attempts[user_key][today][difficulty] = {
        'correct': is_correct,
        'answer': user_answer
    }
    save_user_attempts(attempts)
    
    if is_correct:
        points = {'easy': 1, 'medium': 5, 'hard': 10}[difficulty]
        leaderboard = load_leaderboard()
        existing_user = next((u for u in leaderboard if u['username'].lower() == user_key), None)
        
        if existing_user:
            existing_user['score'] += points
        else:
            leaderboard.append({'username': username, 'score': points})
        
        save_leaderboard(leaderboard)
    
    response = {
        'correct': is_correct,
        'points_earned': {'easy': 1, 'medium': 5, 'hard': 10}[difficulty] if is_correct else 0
    }
    
    if question['answer_type'] == 'numeric':
        response['correct_answer'] = round(question['answer'], 4)
    else:
        response['correct_answer'] = question.get('answer', '')
    
    return jsonify(response)

@app.route('/api/user-status', methods=['POST'])
def get_user_status():
    data = request.get_json()
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({'error': 'Username required'}), 400
    
    today = get_today_string()
    attempts = load_user_attempts()
    user_key = username.lower()
    
    user_attempts = {}
    if user_key in attempts and today in attempts[user_key]:
        user_attempts = attempts[user_key][today]
    
    return jsonify({
        'date': today,
        'attempts': user_attempts
    })

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    leaderboard = load_leaderboard()
    sorted_leaderboard = sorted(leaderboard, key=lambda x: x['score'], reverse=True)[:10]
    return jsonify(sorted_leaderboard)

@app.route('/api/check-username', methods=['POST'])
def check_username():
    data = request.get_json()
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({'available': False, 'error': 'Username required'}), 400
    
    leaderboard = load_leaderboard()
    existing_user = next((u for u in leaderboard if u['username'].lower() == username.lower()), None)
    
    return jsonify({'available': existing_user is None})

@app.route('/api/leaderboard', methods=['POST'])
def update_leaderboard():
    data = request.get_json()
    username = data.get('username', '').strip()
    score = data.get('score', 0)
    
    if not username:
        return jsonify({'error': 'Username required'}), 400
    
    leaderboard = load_leaderboard()
    
    existing_user = next((u for u in leaderboard if u['username'].lower() == username.lower()), None)
    
    if existing_user:
        if score > existing_user['score']:
            existing_user['score'] = score
    else:
        leaderboard.append({'username': username, 'score': score})
    
    save_leaderboard(leaderboard)
    
    sorted_leaderboard = sorted(leaderboard, key=lambda x: x['score'], reverse=True)[:10]
    return jsonify(sorted_leaderboard)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
