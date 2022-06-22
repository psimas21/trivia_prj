import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# Questions Pagination
def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    cur_questions = questions[start:end]

    return cur_questions

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, true')
        response.headers.add('Access-Control-Allow-Methods', 'GET, PATCH, PUT, POST, DELETE, OPTIONS')
        return response
    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.route('/categories', methods=['GET'])
    def fetch_categories():
        selection = Category.query.order_by(Category.id).all()
        cur_categories = paginate_questions(request, selection)

        if len(cur_categories) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'categories': {category.id: category.type for category in selection}
        })

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route('/questions', methods=['GET'])
    def fetch_questions():
        selection = Question.query.order_by(Question.id).all()
        sum_questions = len(selection)
        cur_questions = paginate_questions(request, selection)

        categories = Category.query.order_by(Category.id).all()
        _categories = {}
        for category in categories:
            _categories[category.id] = category.type

        if (len(cur_questions) == 0):
            abort(404)

        return jsonify({
            'success': True,
            'questions': cur_questions,
            'total_questions': sum_questions,
            'categories': _categories
        })

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route('/questions/<int:id>', methods=['DELETE'])
    def del_question(id):

        try:
            question = Question.query.filter_by(id=id).one_or_none()

            if question is None:
                abort(404)

            question.delete()

            return jsonify({
                'success': True,
                'deleted': id
            })

        except:
            abort(422)

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    @app.route("/questions", methods=['POST'])
    def create_individual_question():
        post_body = request.get_json()
        created_question = post_body.get('question', None)
        created_answer = post_body.get('answer', None)
        created_category = post_body.get('category', None)
        created_difficulty = post_body.get('difficulty', None)

        try:
            if len(created_question) == 0 or len(created_difficulty) == 0 or len(created_category) == 0 or len(created_answer) == 0:
                abort(422)
            else:
                new_question = Question(question=created_question, answer=created_answer,
                                        category=created_category, difficulty=created_difficulty)
                new_question.insert()

                selection = Question.query.order_by(Question.id).all()
                current_questions = paginate_questions(request, selection)

                return jsonify({
                    "success": True,
                    "created": new_question.id,
                    "questions": current_questions,
                    "total_questions": len(selection)
                })

        except:
            abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route('/questions/search', methods=['POST'])
    def get_individual_question():
        post_body = request.get_json()
        search_term = post_body.get('search_term', None)

        try:

            if len(search_term) == 0:
                abort(405)
            else:
                selection = Question.query.filter(
                    Question.question.ilike(f'%{search_term}%')).all()
                if selection == []:
                    abort(404)
                else:
                    current_questions = paginate_questions(request, selection)
                    return jsonify({
                        "success": True,
                        "questions": current_questions,
                        "total_questions": len(selection)})

        except:
            abort(422)

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_individual_question_by_category(category_id):
        try:
            selected_category = Category.query.get(category_id)
            if selected_category is None:
                abort(404)
            else:
                selection = Question.query.filter_by(
                    category=selected_category.id).order_by(Question.id).all()
                current_questions = paginate_questions(request, selection)
                return jsonify({
                    "success": True,
                    "questions": current_questions,
                    "current_category": selected_category.type,
                    "total_questions": len(selection)
                })

        except:
            abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/quizes', methods=['POST'])
    def get_individual_question_by_quizes():
        post_body = request.get_json()
        quiz_category = post_body.get('quiz_category', None)
        previous_questions = post_body.get('previous_questions', None)

        try:
            if quiz_category['id'] == 0:
                questions = Question.query.order_by(Question.id).all()
            else:
                questions = Question.query.filter_by(
                    category=quiz_category['id']).order_by(Question.id).all()

            generated_question = random.choice(questions).format()

            is_used = False
            if generated_question['id'] in previous_questions:
                is_used = True

            else:
                return jsonify({
                    "success": True,
                    "question": generated_question})

            while is_used:
                if len(previous_questions) == len(questions):
                    return jsonify({
                        'success': True,
                        'message': "Completed Successfully"
                    })
        except:
            abort(422)

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            'error': 400,
            "message": "Bad request"
        }), 400

    @app.errorhandler(404)
    def page_not_found(error):
        return jsonify({
            "success": False,
            'error': 404,
            "message": "Page not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable_recource(error):
        return jsonify({
            "success": False,
            'error': 422,
            "message": "Unprocessable recource"
        }), 422

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "success": False,
            'error': 500,
            "message": "Internal server error"
        }), 500

    @app.errorhandler(405)
    def invalid_method(error):
        return jsonify({
            "success": False,
            'error': 405,
            "message": "Invalid method!"
        }), 405

    return app

