import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Text } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { CatalogScreen } from './src/screens/CatalogScreen';
import { RackScreen } from './src/screens/RackScreen';
import { BrowserScreen } from './src/screens/BrowserScreen';
import { RootStackParamList } from './src/navigation/types';

const Tab = createBottomTabNavigator();
const RootStack = createNativeStackNavigator<RootStackParamList>();

function TabNavigator() {
  return (
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
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <RootStack.Navigator screenOptions={{ headerShown: false }}>
          <RootStack.Screen name="Tabs" component={TabNavigator} />
          <RootStack.Screen
            name="Browser"
            component={BrowserScreen}
            options={{ presentation: 'fullScreenModal' }}
          />
        </RootStack.Navigator>
      </NavigationContainer>
      <StatusBar style="auto" />
    </SafeAreaProvider>
  );
}
