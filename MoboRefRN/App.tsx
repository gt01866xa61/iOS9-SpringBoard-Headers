import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Text } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { CatalogScreen } from './src/screens/CatalogScreen';
import { RackScreen } from './src/screens/RackScreen';

const Tab = createBottomTabNavigator();

export default function App() {
  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <Tab.Navigator
          screenOptions={({ route }) => ({
            tabBarIcon: ({ color, size }) => {
              const icons: Record<string, string> = {
                Catalog: '🔍',
                Racks: '🗄',
              };
              return (
                <Text style={{ fontSize: size - 4, color }}>{icons[route.name] ?? '?'}</Text>
              );
            },
            tabBarActiveTintColor: '#007AFF',
            tabBarInactiveTintColor: '#999',
            headerStyle: { backgroundColor: '#fff' },
            headerTitleStyle: { fontWeight: '700' },
          })}
        >
          <Tab.Screen
            name="Catalog"
            component={CatalogScreen}
            options={{ title: 'Motherboards' }}
          />
          <Tab.Screen
            name="Racks"
            component={RackScreen}
            options={{ title: 'My Racks' }}
          />
        </Tab.Navigator>
      </NavigationContainer>
      <StatusBar style="auto" />
    </SafeAreaProvider>
  );
}
