import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from .models import Food  
from .models import Contact  
from django.views.decorators.csrf import csrf_exempt
from .models import MealDRI



# Load CSV file once when the server starts
df = pd.read_csv('finalss.csv', on_bad_lines='skip')

def calculate_bmr(age, weight, height, gender):
    if gender.lower() == 'female':
        return 655.1 + (9.563 * weight) + (1.850 * height) - (4.676 * age)
    else:
        return 66.47 + (13.75 * weight) + (5.003 * height) - (6.755 * age)

def calculate_amr(bmr, activity_level):
    activity_multipliers = {
        'sedentary': 1.2,
        'lightly_active': 1.375,
        'moderately_active': 1.55,
        'active': 1.725,
        'very_active': 1.9
    }
    return bmr * activity_multipliers.get(activity_level.lower(), 1.2)

def calculate_dri(age, weight, height, gender, activity_level, goal, meal_type='general'):
    bmr = calculate_bmr(age, weight, height, gender)
    amr = calculate_amr(bmr, activity_level)

    if goal == 'gain':
        calorie_intake = amr + 330
    elif goal == 'loss':
        calorie_intake = amr - 330
    else:
        calorie_intake = amr

    if meal_type == 'breakfast':
        protein_percentage = 0.20
        fat_percentage = 0.25
        carbohydrates_percentage = 0.30
        calorie_percentage = 0.20
    elif meal_type == 'lunch':
        protein_percentage = 0.35
        fat_percentage = 0.40
        carbohydrates_percentage = 0.30
        calorie_percentage = 0.35
    elif meal_type == 'dinner':
        protein_percentage = 0.25
        fat_percentage = 0.25
        carbohydrates_percentage = 0.25
        calorie_percentage = 0.25
    elif meal_type == 'snacks':
        protein_percentage = 0.20
        fat_percentage = 0.10
        carbohydrates_percentage = 0.15
        calorie_percentage = 0.10
    else:
        protein_percentage = 0.068
        fat_percentage = 0.30
        carbohydrates_percentage = 0.55
        calorie_percentage = 0.20

    total_protein = (protein_percentage * calorie_intake) / 4
    total_fat = (fat_percentage * calorie_intake) / 9
    total_carbohydrates = (carbohydrates_percentage * calorie_intake) / 4

    meal_type_percentage = calorie_percentage

    meal_protein = total_protein * meal_type_percentage
    meal_fat = total_fat * meal_type_percentage
    meal_carbohydrates = total_carbohydrates * meal_type_percentage
    meal_calories = calorie_intake * meal_type_percentage




    

    return {
        'total_protein': total_protein,
        'total_fat': total_fat,
        'total_carbohydrates': total_carbohydrates,
        'calorie_intake': calorie_intake,
        'meal_protein': meal_protein,
        'meal_fat': meal_fat,
        'meal_carbohydrates': meal_carbohydrates,
        'meal_calories': meal_calories
    }
def index(request):
    if request.method == 'POST':
        global df

        user_age = int(request.POST['age'])
        user_weight = float(request.POST['weight'])
        user_height = float(request.POST['height'])
        user_gender = request.POST['gender'].lower()
        user_activity_level = request.POST['activity_level'].lower()
        user_goal = request.POST['goal'].lower()
        user_allergy = request.POST['allergy'].lower()

        # Modify this line to handle the 'preference' key gracefully
        user_preference = request.POST.get('preference', '').lower()

        user_keywords = request.POST['keywords'].lower().split(',')

        # Filter dataframe based on allergies
        if user_allergy == 'none':
            df_filtered_allergy = df  # No need to filter if the user has no allergies
        elif user_allergy == 'peanut':
            df_filtered_allergy = df[~df['merged_column'].str.contains('peanut|cashew|almonds|nuts', case=False)]
        elif user_allergy == 'gluten':
            df_filtered_allergy = df[~df['merged_column'].str.contains('gluten|wheat|barley|rye|oat', case=False)]
        elif user_allergy == 'dairy':
            df_filtered_allergy = df[~df['merged_column'].str.contains('dairy|milk|cheese|yogurt|butter|cream|whey|ghee|buttermilk', case=False)]
        elif user_allergy == 'seafood':
            df_filtered_allergy = df[~df['merged_column'].str.contains('seafood|fish|shrimp|salmon|tuna|cod|halibut|crab|lobster|prawn|crayfish|oyster|squid|octopus', case=False)]
        else:
            df_filtered_allergy = df

        if user_preference == 'yes':
            df_filtered_preference = df_filtered_allergy[df_filtered_allergy['Veg/NonVeg'] == 0]  # Filter for vegetarian recipes
        else:
            df_filtered_preference = df_filtered_allergy  # Show all recipes

        dri_results = {}
        recommended_recipes_by_meal = {}  # Initialize this dictionary

        if "na" in user_keywords:
            for meal_type in ['breakfast', 'lunch', 'dinner', 'snacks']:
                dri_results[meal_type] = calculate_dri(user_age, user_weight, user_height, user_gender, user_activity_level, user_goal, meal_type=meal_type)

                user_dri = np.array([dri_results[meal_type][key] for key in ['meal_fat', 'meal_protein', 'meal_carbohydrates', 'meal_calories']])
                recipe_nutrients = df_filtered_preference[['FatContent', 'ProteinContent', 'CarbohydrateContent', 'Calories']].values
                # Use KNeighborsRegressor instead of euclidean_distances
                knn = NearestNeighbors(n_neighbors=20, algorithm='auto')
                knn.fit(recipe_nutrients, np.zeros(recipe_nutrients.shape[0]))  # Fit the model, since KNN does not require labels

                # Predict distances
                distances, top_indices_meal_dri = knn.kneighbors([user_dri])

                top_indices_meal_dri = top_indices_meal_dri[0]  # Initialize top_recipes list here
                top_recipes = []
                for index in top_indices_meal_dri:
                    top_recipes.append({
                        'ID': df_filtered_preference['ID'].iloc[index],
                        'Name': df_filtered_preference['Name'].iloc[index],
                        'FatContent': df_filtered_preference['FatContent'].iloc[index],
                        'ProteinContent': df_filtered_preference['ProteinContent'].iloc[index],
                        'CarbohydrateContent': df_filtered_preference['CarbohydrateContent'].iloc[index],
                        'Calories': df_filtered_preference['Calories'].iloc[index],
                        'RecipeInstructions': df_filtered_preference['RecipeInstructions'].iloc[index],
                        'Images': df_filtered_preference['Images'].iloc[index],
                    })
                recommended_recipes_by_meal[meal_type] = top_recipes
        else:
            # Filter DataFrame based on user keywords
            filtered_by_name = df_filtered_preference[df_filtered_preference['merged_column'].apply(lambda x: any(keyword in x.lower() for keyword in user_keywords))]

            for meal_type in ['breakfast', 'lunch', 'dinner', 'snacks']:
                dri_results[meal_type] = calculate_dri(user_age, user_weight, user_height, user_gender, user_activity_level, user_goal, meal_type=meal_type)
                user_dri = np.array([dri_results[meal_type][key] for key in ['meal_fat', 'meal_protein', 'meal_carbohydrates', 'meal_calories']])
                recipe_nutrients = filtered_by_name[['FatContent', 'ProteinContent', 'CarbohydrateContent', 'Calories']].values
                # Use KNeighborsRegressor instead of euclidean_distances
                knn = NearestNeighbors(n_neighbors=20, algorithm='auto')
                knn.fit(recipe_nutrients, np.zeros(recipe_nutrients.shape[0]))  # Fit the model, since KNN does not require labels

                # Predict distances
                distances, top_indices_meal_dri = knn.kneighbors([user_dri])

                top_indices_meal_dri = top_indices_meal_dri[0]
                top_recipes = []
                for index in top_indices_meal_dri:
                    top_recipes.append({
                        'ID': filtered_by_name['ID'].iloc[index],
                        'Name': filtered_by_name['Name'].iloc[index],
                        'FatContent': filtered_by_name['FatContent'].iloc[index],
                        'ProteinContent': filtered_by_name['ProteinContent'].iloc[index],
                        'CarbohydrateContent': filtered_by_name['CarbohydrateContent'].iloc[index],
                        'Calories': filtered_by_name['Calories'].iloc[index],
                        'RecipeInstructions': filtered_by_name['RecipeInstructions'].iloc[index],
                        'Images': filtered_by_name['Images'].iloc[index],
                    })
                recommended_recipes_by_meal[meal_type] = top_recipes

        context = {
            'dri_results': dri_results,
            'recommended_recipes_by_meal': recommended_recipes_by_meal
        }

                # Save DRI results to the database
        for meal_type, dri_result in dri_results.items():
            MealDRI.objects.create(
                meal_type=meal_type,
                calories=dri_result['meal_calories'],
                protein=dri_result['meal_protein'],
                fat=dri_result['meal_fat'],
                carbohydrates=dri_result['meal_carbohydrates']
            )


        return render(request, 'recommendation.html', context)

    return render(request, 'index.html')



def home(request):
    return render(request, 'index.html')

def contact(request):
    return render(request, 'contact.html')

def form(request):
    return render(request, 'form.html')

def SignupPage(request):
    return render(request, 'home.html')

def LoginPage(request):
    return render(request, 'home.html')

def LogoutPage(request):
    return render(request, 'home.html')

@csrf_exempt  # Disabling CSRF protection for simplicity. Use appropriate CSRF protection in production.
def save_food(request):
    if request.method == 'POST':
        meal_type = request.POST.get('meal_type')
        food_name = request.POST.get('food_name')
        food_id = int(float(request.POST.get('food_id')))  # Convert food_id to float and then int
        
        # Save the food data
        Food.save_food(meal_type, food_name, food_id)

        return JsonResponse({'message': 'Food saved successfully.'})
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)
    


def get_food_details(request):
    global df


        # Retrieve the latest DRI values for all meal types
    latest_dri_values = {
        'breakfast': MealDRI.objects.filter(meal_type='breakfast').latest('id'),
        'lunch': MealDRI.objects.filter(meal_type='lunch').latest('id'),
        'dinner': MealDRI.objects.filter(meal_type='dinner').latest('id'),
        'snacks': MealDRI.objects.filter(meal_type='snacks').latest('id'),
    }



    
    # Initialize an empty dictionary to store food details by meal type
    food_details_by_meal = {}
    
    # Define the meal types
    meal_types = ['breakfast', 'lunch', 'dinner', 'snacks']
    
    # Iterate over each meal type
    for meal_type in meal_types:
        # Retrieve all Food objects for the current meal type
        food_ids = Food.objects.filter(meal_type=meal_type).values_list('food_id', flat=True)
        
        # Initialize an empty dictionary to store food details for the current meal type
        meal_type_food_details = {}
        
        # Iterate over each food ID for the current meal type
        for food_id in food_ids:
            # Search for the food ID in the CSV file
            food_details = df[df['ID'] == food_id][['Name',  'Images',  'Calories', 'FatContent',  'CarbohydrateContent','ProteinContent', 'RecipeInstructions', 'Ingredient' ,'merged_column' ]]
            
            # Convert the food details to a dictionary
            food_details_dict = food_details.iloc[0].to_dict()
            
            # Add the food details to the dictionary for the current meal type
            meal_type_food_details = food_details_dict
        
        # Add the food details for the current meal type to the main dictionary
        food_details_by_meal[meal_type] = meal_type_food_details
    
    # Render the HTML template with the food details and DRI results by meal type
    context = {
        'food_details_by_meal': food_details_by_meal,
         'dri_results': latest_dri_values, 
  
    }
    
    # Render the HTML template with the food details by meal type
    return render(request, 'food_details.html', context)

def graph(request):
     return render(request, 'graph.html')




def contact(request):
    if request.method == 'POST':
        # Get values from form submission
        Name = request.POST.get('Cname')
        Email = request.POST.get('Cemail')
        Subject = request.POST.get('Csubject')
        Message = request.POST.get('Cmessage')



        # Save contact details to Contact model
        contact_model = Contact(Name=Name, Email=Email, Subject=Subject, Message=Message)
        contact_model.save()

        # Redirect to a success page after form submission
        return render(request,'index.html')
    else:
        # Render contact page if request method is not POST
        return render(request, 'index.html')




