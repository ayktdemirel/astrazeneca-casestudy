import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatMenuModule } from '@angular/material/menu';
import { MatBadgeModule } from '@angular/material/badge';
import { AuthService } from '../../services/auth.service';
import { NotificationService } from '../../services/notification.service';

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MatSidenavModule,
    MatToolbarModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
    MatMenuModule,
    MatBadgeModule
  ],
  templateUrl: './layout.html',
  styleUrl: './layout.scss'
})
export class LayoutComponent implements OnInit {
  menuItems = [
    { label: 'Dashboard', icon: 'dashboard', route: '/dashboard' },
    { label: 'Notifications', icon: 'notifications', route: '/notifications' },
    { label: 'Insights', icon: 'insights', route: '/insights' },
    { label: 'Competitors', icon: 'business', route: '/competitors' },
    { label: 'Users', icon: 'group', route: '/users' },
    { label: 'Crawler (Admin)', icon: 'bug_report', route: '/crawler', role: 'ADMIN' }
  ];

  unreadCount$: any;

  constructor(
    public authService: AuthService,
    private notificationService: NotificationService
  ) {
    this.unreadCount$ = this.notificationService.unreadCount$;
  }

  get isAdmin(): boolean {
    return this.authService.isAdmin;
  }

  ngOnInit() {
    this.notificationService.updateUnreadCount();
  }

  logout() {
    this.authService.logout();
  }
}
