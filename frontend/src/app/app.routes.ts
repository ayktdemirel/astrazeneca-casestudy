import { Routes } from '@angular/router';
import { LoginComponent } from './auth/login/login';
import { RegisterComponent } from './auth/register/register';
import { LayoutComponent } from './core/components/layout/layout';
import { DashboardComponent } from './features/dashboard/dashboard';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
    { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
    { path: 'auth/login', component: LoginComponent },
    { path: 'auth/register', component: RegisterComponent },
    {
        path: '',
        component: LayoutComponent,
        canActivate: [authGuard],
        children: [
            { path: 'dashboard', component: DashboardComponent },
            { path: 'notifications', loadComponent: () => import('./features/notifications/notifications').then(m => m.NotificationsComponent) },
            { path: 'insights', loadComponent: () => import('./features/insights/insights').then(m => m.InsightsComponent) },
            { path: 'competitors', loadComponent: () => import('./features/competitors/competitors').then(m => m.CompetitorsComponent) },
            { path: 'users', loadComponent: () => import('./features/users/users').then(m => m.UsersComponent) },
            { path: 'crawler', loadComponent: () => import('./features/crawler/crawler').then(m => m.CrawlerComponent) }
        ]
    },
    { path: '**', redirectTo: 'dashboard' }
];
