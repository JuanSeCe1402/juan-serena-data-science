# Importar las bibliotecas necesarias
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout

# Paso 1: Cargar los datos
# Cargar los datos de entrenamiento y prueba del Titanic
train_data = pd.read_csv('train.csv')
test_data = pd.read_csv('test.csv')

# Paso 2: Preprocesamiento de los datos
# Eliminar columnas irrelevantes o nulas
train_data = train_data.drop(['PassengerId', 'Name', 'Ticket', 'Cabin'], axis=1)
test_data = test_data.drop(['Name', 'Ticket', 'Cabin'], axis=1)

# Codificar variables categóricas
# Convertir variables categóricas (como 'Sex' y 'Embarked') en variables numéricas
train_data = pd.get_dummies(train_data, columns=['Sex', 'Embarked'])
test_data = pd.get_dummies(test_data, columns=['Sex', 'Embarked'])

# Rellenar valores nulos
# Reemplazar los valores nulos en los datos con el promedio de la columna correspondiente
train_data = train_data.fillna(train_data.mean())
test_data = test_data.fillna(test_data.mean())

# Paso 3: Dividir los datos en características y etiquetas
# Extraer las características (X) y las etiquetas (y) de los datos de entrenamiento
X = train_data.drop('Survived', axis=1).values
y = train_data['Survived'].values

# Paso 4: Dividir los datos en conjuntos de entrenamiento y prueba
# Dividir los datos en conjuntos de entrenamiento y prueba para evaluar el modelo
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Paso 5: Normalizar las características
# Escalar las características para que tengan un rango similar y evitar sesgos
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Paso 6: Construir el modelo
# Crear un modelo secuencial de Keras y agregar capas al mismo
model = Sequential()
model.add(Dense(64, activation='relu', input_dim=X_train.shape[1]))
model.add(Dropout(0.5))
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(1, activation='sigmoid'))

# Paso 7: Compilar y entrenar el modelo
# Configurar el modelo con la función de pérdida, el optimizador y las métricas
model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
model.fit(X_train, y_train, epochs=50, batch_size=32, verbose=1)

# Paso 8: Evaluar el modelo
# Evaluar el rendimiento del modelo en los datos de prueba
loss, accuracy = model.evaluate(X_test, y_test)
print('Loss:', loss)
print('Accuracy:', accuracy)

# Paso 9: Hacer predicciones
# Utilizar el modelo entrenado para hacer predicciones en los datos de prueba
X_submission = test_data.drop('PassengerId', axis=1).values
X_submission = scaler.transform(X_submission)
predictions = model
predictions = model.predict(X_submission)

# Crear un DataFrame con las predicciones
submission = pd.DataFrame({'PassengerId': test_data['PassengerId'], 'Survived': np.squeeze(predictions)})

# Guardar las predicciones en un archivo CSV
submission.to_csv('submission.csv', index=False)
