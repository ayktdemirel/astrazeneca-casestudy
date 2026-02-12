import { Component, Inject, Optional } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';

export interface InsightFormData {
    mode: 'create' | 'edit';
    insight: {
        id?: string;
        title: string;
        description: string;
        category: string;
        therapeuticArea: string;
        impactLevel: string;
        relevanceScore: number | null;
        source: string;
        competitorId: string;
    };
}

@Component({
    selector: 'app-insight-form-dialog',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        MatDialogModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatButtonModule
    ],
    template: `
    <div class="p-4" style="min-width: 450px;">
      <h2 class="text-xl font-bold text-gray-800 mb-6">{{ isEdit ? 'Edit Insight' : 'Add New Insight' }}</h2>

      <div class="space-y-4">
        <mat-form-field appearance="outline" class="w-full">
          <mat-label>Title</mat-label>
          <input matInput [(ngModel)]="insight.title" required>
        </mat-form-field>

        <mat-form-field appearance="outline" class="w-full">
          <mat-label>Description</mat-label>
          <textarea matInput [(ngModel)]="insight.description" rows="4"></textarea>
        </mat-form-field>

        <div class="grid grid-cols-2 gap-4">
          <mat-form-field appearance="outline">
            <mat-label>Category</mat-label>
            <mat-select [(ngModel)]="insight.category">
              <mat-option value="Pipeline">Pipeline</mat-option>
              <mat-option value="Regulatory">Regulatory</mat-option>
              <mat-option value="Commercial">Commercial</mat-option>
              <mat-option value="Clinical Trial">Clinical Trial</mat-option>
              <mat-option value="Market Access">Market Access</mat-option>
              <mat-option value="Other">Other</mat-option>
            </mat-select>
          </mat-form-field>

          <mat-form-field appearance="outline">
            <mat-label>Therapeutic Area</mat-label>
            <mat-select [(ngModel)]="insight.therapeuticArea">
              <mat-option value="Oncology">Oncology</mat-option>
              <mat-option value="Cardiovascular">Cardiovascular</mat-option>
              <mat-option value="Respiratory">Respiratory</mat-option>
              <mat-option value="Immunology">Immunology</mat-option>
              <mat-option value="Neuroscience">Neuroscience</mat-option>
              <mat-option value="Rare Diseases">Rare Diseases</mat-option>
            </mat-select>
          </mat-form-field>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <mat-form-field appearance="outline">
            <mat-label>Impact Level</mat-label>
            <mat-select [(ngModel)]="insight.impactLevel">
              <mat-option value="High">High</mat-option>
              <mat-option value="Medium">Medium</mat-option>
              <mat-option value="Low">Low</mat-option>
            </mat-select>
          </mat-form-field>

          <mat-form-field appearance="outline">
            <mat-label>Relevance Score (0-10)</mat-label>
            <input matInput type="number" [(ngModel)]="insight.relevanceScore" min="0" max="10" step="0.5">
          </mat-form-field>
        </div>

        <mat-form-field appearance="outline" class="w-full">
          <mat-label>Source</mat-label>
          <input matInput [(ngModel)]="insight.source" placeholder="e.g. FDA, Reuters, ClinicalTrials.gov">
        </mat-form-field>
      </div>

      <div class="flex justify-end gap-2 mt-6">
        <button mat-button (click)="cancel()">Cancel</button>
        <button mat-raised-button color="primary"
          [disabled]="!insight.title"
          (click)="submit()">
          {{ isEdit ? 'Save Changes' : 'Create Insight' }}
        </button>
      </div>
    </div>
  `
})
export class InsightFormDialogComponent {
    isEdit = false;
    insight: InsightFormData['insight'] = {
        title: '',
        description: '',
        category: '',
        therapeuticArea: '',
        impactLevel: '',
        relevanceScore: null,
        source: '',
        competitorId: ''
    };

    constructor(
        private dialogRef: MatDialogRef<InsightFormDialogComponent>,
        @Optional() @Inject(MAT_DIALOG_DATA) public data: InsightFormData
    ) {
        if (data && data.mode === 'edit') {
            this.isEdit = true;
            this.insight = { ...data.insight };
        }
    }

    cancel() {
        this.dialogRef.close();
    }

    submit() {
        this.dialogRef.close({ ...this.insight, mode: this.isEdit ? 'edit' : 'create' });
    }
}
